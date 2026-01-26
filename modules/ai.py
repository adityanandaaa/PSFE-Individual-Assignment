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

    Returns (score:int, advice:str). If the configured AI package or network
    call fails, a sensible fallback is returned.
    """
    # Safe fallback
    fallback_score = 70
    fallback_advice = (
        "Based on your data, focus on reducing Wants to increase Savings. "
        "Consider budgeting apps for tracking."
    )

    if genai is None:
        logging.warning("No Google GenAI package available; using fallback advice.")
        return fallback_score, fallback_advice

    try:
        # Try to use the newer `google.genai` interface if available.
        prompt_payload = {
            "role": "Senior Financial Consultant specializing in 50/30/20",
            "income": income,
            "buckets": {"needs": needs, "wants": wants, "savings": savings},
            "top_categories": top_wants,
            "goal": "Achieve 20% savings target"
        }
        prompt = f"Analyze this financial data: {json.dumps(prompt_payload)}. Provide a health score 0-100 and 3 actionable tips."

        if GENAI_PKG == 'genai':
            # Preferred modern client access: genai.Client().generate(...)
            client_cls = getattr(genai, 'Client', None)
            if client_cls:
                client = client_cls()
                # Use the recommended generate interface with model name
                try:
                    resp = client.generate(model="gemini-2.5-flash", input=prompt)
                except TypeError:
                    # Older genai versions might use 'text' or 'prompt' argument
                    resp = client.generate(model="gemini-2.5-flash", prompt=prompt)

                # resp may have candidates or text depending on version
                if hasattr(resp, 'candidates') and resp.candidates:
                    # candidate objects often have 'output' or 'content'
                    first = resp.candidates[0]
                    text = getattr(first, 'output', None) or getattr(first, 'content', None) or str(first)
                else:
                    text = getattr(resp, 'output', None) or getattr(resp, 'text', None) or str(resp)

            elif hasattr(genai, 'configure'):
                # Some older genai releases expose a configure + GenerativeModel
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
            # Fallback to the older (deprecated) package interface
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

        # Parse score and advice (simple parsing)
        lines = text.split('\n')
        score = 75  # Default
        for line in lines:
            if 'score' in line.lower() or 'health' in line.lower():
                nums = re.findall(r'\d+', line)
                if nums:
                    score = int(nums[0])
                    break
        advice = text
        return score, advice

    except Exception as e:
        logging.error(f"AI error: {str(e)}")
        return fallback_score, fallback_advice