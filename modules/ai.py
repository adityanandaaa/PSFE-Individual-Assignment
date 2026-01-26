"""AI integration wrapper.

This module attempts to use `google.genai` if available, falling back to the
deprecated `google.generativeai` package. All external calls are wrapped so
failures return a safe fallback response for offline/testing environments.
"""

import json
import logging
import re
import os

# Prefer the newer package if present.
try:
    import google.genai as genai
    GENAI_PKG = 'genai'
except Exception:
    try:
        import google.generativeai as genai
        GENAI_PKG = 'generativeai'
    except Exception:
        genai = None
        GENAI_PKG = None


def get_ai_insights(income, needs, wants, savings, top_wants):
    """Get AI insights with safe fallback.
    
    Calls the Gemini API to analyze financial data and provide personalized advice.
    If API is unavailable, returns sensible fallback recommendations.

    Args:
        income: Total monthly income
        needs: Total needs spending (50% target)
        wants: Total wants spending (30% target)
        savings: Total savings (20% target)
        top_wants: Dict of top spending categories in wants
        
    Returns:
        tuple: (score: int [0-100], advice: str with recommendations)
    """
    # === FALLBACK VALUES ===
    # Used when API is unavailable or fails
    fallback_score = 70
    fallback_advice = (
        "Based on your data, focus on reducing Wants to increase Savings. "
        "Consider budgeting apps for tracking."
    )

    # Check if any Google GenAI package is available
    if genai is None:
        logging.warning("No Google GenAI package available; using fallback advice.")
        return fallback_score, fallback_advice

    try:
        # === BUILD ANALYSIS PROMPT ===
        # Create a structured payload with financial data for AI analysis
        prompt_payload = {
            "role": "Senior Financial Consultant specializing in 50/30/20",
            "income": income,
            "buckets": {"needs": needs, "wants": wants, "savings": savings},
            "top_categories": top_wants,
            "goal": "Achieve 20% savings target"
        }
        # Format prompt for the API
        prompt = f"Analyze this financial data: {json.dumps(prompt_payload)}. Provide a health score 0-100 and 3 actionable tips."

        # === ATTEMPT MODERN GENAI CLIENT ===
        if GENAI_PKG == 'genai':
            # Preferred modern client access: genai.Client().generate(...)
            client_cls = getattr(genai, 'Client', None)
            if client_cls:
                # Initialize client and attempt to generate response
                client = client_cls()
                # Try modern argument name first ('input'), fallback to 'prompt'
                try:
                    resp = client.generate(model="gemini-2.5-flash", input=prompt)
                except TypeError:
                    # Older genai versions might use 'text' or 'prompt' argument
                    resp = client.generate(model="gemini-2.5-flash", prompt=prompt)

                # Extract text from response (structure varies by version)
                if hasattr(resp, 'candidates') and resp.candidates:
                    # candidate objects often have 'output' or 'content'
                    first = resp.candidates[0]
                    text = getattr(first, 'output', None) or getattr(first, 'content', None) or str(first)
                else:
                    # Try direct text attributes
                    text = getattr(resp, 'output', None) or getattr(resp, 'text', None) or str(resp)

            elif hasattr(genai, 'configure'):
                # Fallback for older genai releases that expose configure + GenerativeModel
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                    except Exception as e:
                        logging.warning(f"genai.configure failed: {e}")
                else:
                    logging.warning("Environment variable GEMINI_API_KEY not set; genai may not be configured.")
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                text = getattr(response, 'text', str(response))
            else:
                raise RuntimeError("Unsupported genai client interface")
        else:
            # === FALLBACK TO DEPRECATED PACKAGE ===
            # Use the older (deprecated) google.generativeai package
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                except Exception as e:
                    logging.warning(f"genai.configure failed: {e}")
            else:
                logging.warning("Environment variable GEMINI_API_KEY not set; genai may not be configured.")
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text = getattr(response, 'text', str(response))

        # === PARSE RESPONSE ===
        # Extract health score from AI response using regex
        lines = text.split('\n')
        score = 75  # Default score if parsing fails
        for line in lines:
            # Look for score/health keywords in response
            if 'score' in line.lower() or 'health' in line.lower():
                # Extract first number found in the line
                nums = re.findall(r'\d+', line)
                if nums:
                    score = int(nums[0])
                    break
        # Use full response as advice
        advice = text
        return score, advice

    except Exception as e:
        # Log error and return fallback values
        logging.error(f"AI error: {str(e)}")
        return fallback_score, fallback_advice