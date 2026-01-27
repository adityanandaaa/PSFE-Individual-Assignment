"""AI integration wrapper.

This module provides financial advice using the Gemini API.
Health score is calculated using our own 50/30/20 logic formula.
"""

import asyncio
import json
import logging
import re
import os
from finance_app.logic import calculate_health_score
from finance_app.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)

# Import the modern google-genai package
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False
    logger.warning("google-genai package not available; AI advice will use fallback mode.")


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


async def get_ai_insights(income, needs, wants, savings, top_wants):
    """Get AI advice with health score from our own logic (async).
    
    Uses our mathematical 50/30/20 formula to calculate health score.
    Calls Gemini API asynchronously for personalized financial advice.
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
        logger.warning("No Google GenAI package available; using fallback advice.")
        return score, fallback_advice

    try:
        # === BUILD ENHANCED PROMPT PAYLOAD ===
        # Create a comprehensive, structured payload with detailed financial metrics
        # This enables the AI to provide more nuanced, context-aware insights
        
        # Calculate additional metrics for richer analysis
        needs_ratio = needs / income if income else 0
        wants_ratio = wants / income if income else 0
        savings_ratio = savings / income if income else 0
        
        # Calculate deviations from 50/30/20 targets for clarity
        needs_deviation = needs_ratio - 0.50
        wants_deviation = wants_ratio - 0.30
        savings_deviation = savings_ratio - 0.20
        
        # Total categorized spending (should equal income if all spent)
        total_categorized = needs + wants + savings
        uncategorized = max(0, income - total_categorized)
        
        # Determine health status category
        if score >= 80:
            health_status = "Excellent - Well-balanced budget"
        elif score >= 60:
            health_status = "Good - Room for optimization"
        else:
            health_status = "Fair - Significant rebalancing needed"
        
        # Build comprehensive prompt payload for AI analysis
        prompt_payload = {
            # === PROFILE INFORMATION ===
            "user_profile": {
                "role": "Individual seeking financial optimization using 50/30/20 methodology",
                "goal": "Achieve optimal 50/30/20 budget allocation",
                "health_status": health_status
            },
            
            # === FINANCIAL OVERVIEW ===
            "financial_overview": {
                "monthly_income": income,
                "total_tracked_spending": total_categorized,
                "untracked_amount": uncategorized,
                "coverage_percentage": (total_categorized / income * 100) if income else 0
            },
            
            # === BUDGET BREAKDOWN (Absolute Amounts) ===
            "budget_breakdown": {
                "needs": {
                    "amount": needs,
                    "percentage_of_income": round(needs_ratio * 100, 1),
                    "target_percentage": 50
                },
                "wants": {
                    "amount": wants,
                    "percentage_of_income": round(wants_ratio * 100, 1),
                    "target_percentage": 30
                },
                "savings": {
                    "amount": savings,
                    "percentage_of_income": round(savings_ratio * 100, 1),
                    "target_percentage": 20
                }
            },
            
            # === DEVIATION ANALYSIS ===
            "deviation_analysis": {
                "needs": {
                    "deviation_from_target": round(needs_deviation * 100, 1),
                    "status": "OVER" if needs_deviation > 0 else "UNDER",
                    "needed_adjustment": round(abs(needs_deviation) * income, 2)
                },
                "wants": {
                    "deviation_from_target": round(wants_deviation * 100, 1),
                    "status": "OVER" if wants_deviation > 0 else "UNDER",
                    "needed_adjustment": round(abs(wants_deviation) * income, 2)
                },
                "savings": {
                    "deviation_from_target": round(savings_deviation * 100, 1),
                    "status": "UNDER" if savings_deviation < 0 else "OVER",
                    "needed_adjustment": round(abs(savings_deviation) * income, 2)
                }
            },
            
            # === TOP SPENDING CATEGORIES (for pattern analysis) ===
            "top_wants_categories": {
                category: {
                    "amount": amount,
                    "percentage_of_wants": round((amount / wants * 100) if wants else 0, 1),
                    "percentage_of_income": round((amount / income * 100) if income else 0, 1)
                }
                # Limit to top 3 to reduce prompt size for free tier
                for category, amount in list(top_wants.items())[:3]
            },
            
            # === HEALTH SCORE DETAILS ===
            "health_metrics": {
                "overall_score": score,
                "score_out_of": 100,
                "score_category": health_status,
                "calculation_method": "Weighted deviation model (Needs: 20%, Wants: 50%, Savings: 60%)"
            },
            
            # === PRIORITIZATION GUIDANCE ===
            "priority_areas": {
                "primary_focus": _determine_priority(needs_deviation, wants_deviation, savings_deviation),
                "secondary_focus": _determine_secondary_priority(needs_deviation, wants_deviation, savings_deviation),
                "improvement_potential": round(((100 - score) / 100) * income, 2)
            }
        }
        
        # === BUILD COMPACT, HIGH-QUALITY PROMPT (reduced tokens) ===
        # Use compact JSON (no spaces) and concise instructions to lower input tokens
        prompt_json = json.dumps(prompt_payload, separators=(",", ":"), ensure_ascii=False)
        prompt = (
            "You are a 50/30/20 financial advisor. Based on the payload, provide:\n"
            "- Current state assessment\n"
            "- 3 specific recommendations with quantified impact\n"
            "- 1 quick win and 1 long-term habit\n"
            "Respond with clear headers and bullets. Keep it concise.\n"
            "PAYLOAD:\n" + prompt_json
        )

        # === USE MODERN GENAI CLIENT API ===
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("Environment variable GEMINI_API_KEY not set; using fallback advice.")
            return score, fallback_advice
        
        # Initialize the client with API key (matches test_async_gemini.py pattern)
        client = genai.Client(api_key=api_key)
        
        # Generate content using the modern async API with enhanced parameters
        # Use client.aio.models.generate_content for async calls
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.95,        # Diverse but focused responses
                top_k=40,          # Limit vocabulary for coherence
                max_output_tokens=300  # Reduce output tokens for free tier
            ),
            timeout=15.0  # 15-second timeout to prevent indefinite hangs
        )
        
        # Check for truncation due to max_output_tokens
        if hasattr(response, 'candidates') and response.candidates:
            finish_reason = response.candidates[0].finish_reason
            if finish_reason == types.FinishReason.MAX_TOKENS:
                logger.info("AI response truncated at 300 tokens (max_output_tokens limit)")
        
        # Extract text from response
        if response and response.text:
            advice = response.text
        else:
            logger.warning("Empty response from AI; using fallback advice.")
            advice = fallback_advice

        # === USE AI RESPONSE AS ADVICE ===
        # Return our calculated score with AI-generated advice
        return score, advice

    except Exception as e:
        # Log error without exposing sensitive financial data
        logger.error(f"AI request failed, using fallback advice: {type(e).__name__}")
        return score, fallback_advice


def _determine_priority(needs_deviation, wants_deviation, savings_deviation):
    """Determine the primary focus area based on deviations.
    
    Args:
        needs_deviation (float): Needs ratio deviation from 50% target
        wants_deviation (float): Wants ratio deviation from 30% target
        savings_deviation (float): Savings ratio deviation from 20% target
        
    Returns:
        str: Primary area to focus on
    """
    # Prioritize based on severity and impact
    issues = [
        ("reduce_needs", abs(needs_deviation), needs_deviation > 0),
        ("reduce_wants", abs(wants_deviation), wants_deviation > 0),
        ("increase_savings", abs(savings_deviation), savings_deviation < 0)
    ]
    
    # Sort by deviation magnitude and filter for actual problems
    critical_issues = [(issue, magnitude) for issue, magnitude, is_problem in issues if is_problem]
    critical_issues.sort(key=lambda x: x[1], reverse=True)
    
    if critical_issues:
        return critical_issues[0][0]
    return "optimize_all_categories"


def _determine_secondary_priority(needs_deviation, wants_deviation, savings_deviation):
    """Determine the secondary focus area.
    
    Args:
        needs_deviation (float): Needs ratio deviation from 50% target
        wants_deviation (float): Wants ratio deviation from 30% target
        savings_deviation (float): Savings ratio deviation from 20% target
        
    Returns:
        str: Secondary area to focus on
    """
    # Build list of areas needing improvement
    issues = [
        ("reduce_needs", abs(needs_deviation), needs_deviation > 0),
        ("reduce_wants", abs(wants_deviation), wants_deviation > 0),
        ("increase_savings", abs(savings_deviation), savings_deviation < 0)
    ]
    
    # Sort by deviation magnitude and filter for actual problems
    critical_issues = [(issue, magnitude) for issue, magnitude, is_problem in issues if is_problem]
    critical_issues.sort(key=lambda x: x[1], reverse=True)
    
    if len(critical_issues) > 1:
        return critical_issues[1][0]
    elif critical_issues:
        return critical_issues[0][0]
    return "maintain_current_balance"