"""AI integration wrapper.

This module provides financial advice using the Gemini API.
Health score is calculated using our own 50/30/20 logic formula.
"""

import json
import logging
import re
import os
from finance_app.logic import calculate_health_score

# Import the modern google-genai package
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False
    logging.warning("google-genai package not available; AI advice will use fallback mode.")


def _build_fallback_advice(score, income, needs, wants, savings, top_wants):
    """Return one of several deterministic fallback messages based on score buckets.

    We keep messages deterministic (no randomness) to aid testing and reproducibility.
    """
    needs_pct = needs / income * 100 if income else 0
    wants_pct = wants / income * 100 if income else 0
    savings_pct = savings / income * 100 if income else 0
    top_wants_text = ", ".join(f"{k}: {v/income*100:.1f}%" for k, v in list(top_wants.items())[:3]) if top_wants else "No dominant wants categories"

    templates = [
        "Based on your 50/30/20 analysis, tighten wants spending and lift savings to reach your 20% target."
        f" Needs: {needs_pct:.1f}% (50% target), Wants: {wants_pct:.1f}% (30% target), Savings: {savings_pct:.1f}% (20% target).",
        "Your score shows room to rebalance: trim non-essentials and redirect to savings until you hit 20%."
        f" Current split — Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "Focus on two actions: reduce wants by 5–10% and move that to savings; keep needs near 50%."
        f" Snapshot: Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "Bring wants closer to 30% and push savings toward 20%. Start with your top wants categories: "
        f"{top_wants_text}.",
        "Solid start. Nudge savings up by trimming the largest wants categories and automate a monthly transfer to savings."
        f" Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "Good balance. To reach Excellent, aim for Wants ≤30% and Savings ≥20%. Keep Needs near 50%."
        f" Current: Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "Efficiency tweak: freeze 1–2 discretionary categories for 30 days and divert that amount to savings."
        f" Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "If income is volatile, pre-commit a fixed savings % on payday and cap wants at 30%."
        f" Present mix: Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
        "Close the gap by targeting the top 3 wants categories: "
        f"{top_wants_text}. Reallocate at least half of those amounts to savings.",
        "Great trajectory. Lock in a minimum 20% savings auto-transfer and keep wants under 30% to maintain an Excellent score."
        f" Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%.",
    ]

    # Bucket by score to keep advice consistent: lower scores get earlier items, higher scores later.
    if score < 40:
        idx = 0
    elif score < 55:
        idx = 1
    elif score < 65:
        idx = 2
    elif score < 70:
        idx = 3
    elif score < 75:
        idx = 4
    elif score < 80:
        idx = 5
    elif score < 85:
        idx = 6
    elif score < 90:
        idx = 7
    elif score < 95:
        idx = 8
    else:
        idx = 9

    return templates[idx]


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
    fallback_advice = _build_fallback_advice(score, income, needs, wants, savings, top_wants)

    # Check if any Google GenAI package is available
    if not GENAI_AVAILABLE:
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

        # === USE MODERN GENAI CLIENT API ===
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logging.warning("Environment variable GEMINI_API_KEY not set; using fallback advice.")
            return score, fallback_advice
        
        # Initialize the client with API key
        client = genai.Client(api_key=api_key)
        
        # Generate content using the modern API
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        # Extract text from response
        if response and response.text:
            advice = response.text
        else:
            logging.warning("Empty response from AI; using fallback advice.")
            advice = fallback_advice

        # === USE AI RESPONSE AS ADVICE ===
        # Return our calculated score with AI-generated advice
        return score, advice

    except Exception as e:
        # Log error and return score with fallback advice
        logging.error(f"AI error: {str(e)}")
        return score, fallback_advice