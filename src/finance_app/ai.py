"""AI integration wrapper.

This module provides financial advice using the Gemini API.
Health score is calculated using our own 50/30/20 logic formula.
"""

import json
import logging
import re
import os
from finance_app.logic import calculate_health_score

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
    """Get AI advice with health score from our own logic.
    
    Uses our mathematical 50/30/20 formula to calculate health score.
    Calls Gemini API only for personalized financial advice.
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
    # === CALCULATE HEALTH SCORE USING OUR LOGIC ===
    # This is deterministic and doesn't depend on API availability
    score = calculate_health_score(income, needs, wants, savings)
    
    # === FALLBACK ADVICE ===
    # Used when API is unavailable or fails
    fallback_advice = (
        "Based on your 50/30/20 analysis:\n"
        f"Needs: {needs/income*100:.1f}% (target: 50%)\n"
        f"Wants: {wants/income*100:.1f}% (target: 30%)\n"
        f"Savings: {savings/income*100:.1f}% (target: 20%)\n\n"
        "Focus on aligning your spending with these targets to improve your financial health."
    )

    # Check if any Google GenAI package is available
    if genai is None:
        logging.warning("No Google GenAI package available; using fallback advice.")
        return score, fallback_advice

    try:
        # === BUILD ADVICE PROMPT ===
        # Create a structured payload with financial data for AI analysis
        prompt_payload = {
            "role": "Senior Financial Consultant specializing in 50/30/20",
            "income": income,
            "buckets": {"needs": needs, "wants": wants, "savings": savings},
            "top_categories": top_wants,
            "goal": "Achieve 20% savings target",
            "calculated_score": score
        }
        # Format prompt for the API - ask for advice only, not score
        prompt = f"I have a financial health score of {score}/100 based on this data: {json.dumps(prompt_payload)}. Provide 3 specific, actionable tips to improve my financial health and reach my savings goal."

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

        # === USE AI RESPONSE AS ADVICE ===
        # Return our calculated score with AI-generated advice
        advice = text
        return score, advice

    except Exception as e:
        # Log error and return score with fallback advice
        logging.error(f"AI error: {str(e)}")
        return score, fallback_advice