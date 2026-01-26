import google.generativeai as genai
import json
import logging
import re

def get_ai_insights(income, needs, wants, savings, top_wants):
    """Get AI insights with fallback."""
    try:
        genai.configure(api_key="AIzaSyBb4ZnoMT_t_LIZ1jOGX_xbw6GIqzil03g")  # Use the provided key
        model = genai.GenerativeModel('gemini-2.0-flash')
        payload = {
            "role": "Senior Financial Consultant specializing in 50/30/20",
            "income": income,
            "buckets": {"needs": needs, "wants": wants, "savings": savings},
            "top_categories": top_wants,
            "goal": "Achieve 20% savings target"
        }
        prompt = f"Analyze this financial data: {json.dumps(payload)}. Provide a health score 0-100 and 3 tips."
        response = model.generate_content(prompt)
        text = response.text
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
        # Fallback advice
        score = 70
        advice = "Based on your data, focus on reducing Wants to increase Savings. Consider budgeting apps for tracking."
        return score, advice