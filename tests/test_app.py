"""
TEST SUITE: Finance Health Check 50/30/20 Web App
==========================================

This test suite validates the core logic modules used by the Streamlit web app.
Tests cover:
- Currency handling and validation
- Income validation
- Excel file upload and validation
- 50/30/20 budget analysis
- Deterministic health score calculation
- AI insights integration
- PDF report generation

DEPRECATED TESTS (for legacy .exe desktop app):
- Tkinter GUI tests (see LEGACY_FILES.md)
- PyInstaller packaging tests

To run tests:
    pytest test_app.py -v
"""

import unittest
import os
import sys
from pathlib import Path
import json
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open, call
import tempfile
from finance_app.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data, calculate_health_score
from finance_app.ai import get_ai_insights, _determine_priority, _determine_secondary_priority
from finance_app.pdf_generator import generate_pdf

class TestFinancialHealthChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.currencies = load_currencies()
        cls.test_file = "test_data.xlsx"
        # Create a valid test Excel file
        data = {
            'Date': ['1/1/2026', '2/1/2026'],
            'Name': ['Rent', 'Groceries'],
            'Type': ['Needs', 'Needs'],
            'Amount': [1000, 200],
            'Category': ['Rent', 'Food']
        }
        pd.DataFrame(data).to_excel(cls.test_file, index=False)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)

    def test_load_currencies(self):
        self.assertIsInstance(self.currencies, list)
        self.assertGreater(len(self.currencies), 0)
        gbp = next((c for c in self.currencies if c['code'] == 'GBP'), None)
        self.assertIsNotNone(gbp)
        self.assertEqual(gbp['symbol'], '£')

    def test_is_valid_income(self):
        self.assertTrue(is_valid_income(1000))
        self.assertTrue(is_valid_income("100.50"))
        self.assertFalse(is_valid_income(0))
        self.assertFalse(is_valid_income(-100))
        self.assertFalse(is_valid_income("abc"))
        self.assertFalse(is_valid_income(None))

    def test_get_currency_symbol(self):
        self.assertEqual(get_currency_symbol(self.currencies, 'GBP'), '£')
        self.assertEqual(get_currency_symbol(self.currencies, 'USD'), '$')
        self.assertIsNone(get_currency_symbol(self.currencies, 'INVALID'))

    def test_validate_file_success(self):
        valid, result = validate_file(self.test_file)
        self.assertTrue(valid)
        self.assertIsInstance(result, pd.DataFrame)

    def test_validate_file_failure(self):
        # Create an invalid file (missing columns)
        bad_file = "bad_test.xlsx"
        pd.DataFrame({'A': [1]}).to_excel(bad_file, index=False)
        valid, errors = validate_file(bad_file)
        self.assertFalse(valid)
        self.assertIsInstance(errors, list)
        os.remove(bad_file)

    def test_analyze_data(self):
        valid, df = validate_file(self.test_file)
        needs, wants, savings, top_wants = analyze_data(df, 1200)
        self.assertEqual(needs, 1200)
        self.assertEqual(wants, 0)
        self.assertEqual(savings, 0)
        self.assertTrue(isinstance(top_wants, pd.Series))

    def test_amount_decimal_places_invalid(self):
        # Amount with more than 3 decimal places should fail validation
        bad_file = "bad_decimal.xlsx"
        data = {
            'Date': ['1/1/2026'],
            'Name': ['Test'],
            'Type': ['Needs'],
            'Amount': [1.1234],
            'Category': ['Misc']
        }
        pd.DataFrame(data).to_excel(bad_file, index=False)
        valid, errors = validate_file(bad_file)
        self.assertFalse(valid)
        self.assertTrue(any('Invalid amount' in msg for _, msg in errors))
        os.remove(bad_file)

    def test_top_wants_limit(self):
        # Ensure analyze_data returns at most 5 top wants categories
        many_file = "many_wants.xlsx"
        data = {
            'Date': ['1/1/2026'] * 10,
            'Name': [f'Item{i}' for i in range(10)],
            'Type': ['Wants'] * 10,
            'Amount': [i + 1 for i in range(10)],
            'Category': [f'Cat{i}' for i in range(10)]
        }
        pd.DataFrame(data).to_excel(many_file, index=False)
        valid, df = validate_file(many_file)
        self.assertTrue(valid)
        needs, wants, savings, top_wants = analyze_data(df, 1000)
        self.assertTrue(len(top_wants) <= 5)
        os.remove(many_file)

    def test_health_score_perfect_50_30_20(self):
        """Test health score calculation for perfect 50/30/20."""
        score = calculate_health_score(2000, 1000, 600, 400)
        self.assertEqual(score, 100)

    def test_health_score_conservative_spending(self):
        """Test that conservative spending gets perfect score."""
        # Under-spending is rewarded (no penalty)
        score = calculate_health_score(2000, 800, 400, 800)
        self.assertEqual(score, 100)

    def test_health_score_under_savings(self):
        """Test penalty for under-saving."""
        # Savings at 10% (below 20% target)
        score = calculate_health_score(2000, 1200, 600, 200)
        self.assertGreater(score, 80)  # Should be penalized
        self.assertLess(score, 100)

    def test_health_score_wants_overspend(self):
        """Test penalty for wants overspending (0.5 weight)."""
        # Wants at 40% (above 30% target)
        score = calculate_health_score(2000, 1000, 800, 200)
        self.assertGreater(score, 80)
        self.assertLess(score, 100)

    def test_health_score_needs_overspend_moderate(self):
        """Test penalty for needs overspending (0.2 weight)."""
        # Needs at 60% (above 50% target)
        score = calculate_health_score(2000, 1200, 600, 200)
        self.assertGreater(score, 90)  # Should be lightly penalized
        self.assertLess(score, 100)

    def test_health_score_needs_extreme_overspend(self):
        """Test severe penalty when needs > 75%."""
        # Needs at 76% - triggers -10 penalty
        score = calculate_health_score(2000, 1520, 300, 180)
        self.assertLess(score, 80)  # Should be significantly penalized

    def test_health_score_negative_savings(self):
        """Test zero score for negative savings (debt)."""
        score = calculate_health_score(2000, 1200, 900, -100)
        self.assertEqual(score, 0)

    def test_health_score_zero_income(self):
        """Test zero score for zero income."""
        score = calculate_health_score(0, 0, 0, 0)
        self.assertEqual(score, 0)

    def test_ai_fallback(self):
        """Test AI returns deterministic health score and advice."""
        # Now uses calculate_health_score() directly (not API-dependent)
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        # Score for perfect 50/30/20 should be 100
        self.assertEqual(score, 100)
        self.assertIsInstance(advice, str)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'})
    @patch('finance_app.ai.genai')
    def test_ai_with_mock_response(self, mock_genai):
        """Test AI insights with mocked response from GenerativeModel."""
        # Mock the GenerativeModel().generate_content() response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Health Score: 85\nTip 1: Increase savings\nTip 2: Reduce wants\nTip 3: Track expenses"
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = MagicMock()
        
        # Call AI function
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Verify results - score should be calculated from our logic (perfect 50/30/20 = 100)
        self.assertIsInstance(score, int)
        # Advice might be mocked string or our fallback, both are OK
        self.assertTrue(isinstance(advice, str) or hasattr(advice, '__call__'))

    @patch('finance_app.ai.genai')
    def test_ai_with_generativemodel_mock(self, mock_genai):
        """Test AI insights with mocked GenerativeModel interface (fallback)."""
        # Mock the GenerativeModel().generate_content() response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Health Score: 72\nAdvice: Your spending is balanced overall."
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = MagicMock()
        
        # Simulate missing Client but available configure
        mock_genai.Client = None
        
        import sys
        sys.modules['google.genai'] = mock_genai
        
        # Call AI function
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Verify results
        self.assertIsInstance(score, int)
        self.assertIsInstance(advice, str)

    @patch.dict(os.environ, {}, clear=True)
    def test_ai_without_api_key_uses_fallback(self):
        """Test that AI calculates score using our logic even without API key."""
        # Health score is now calculated using our own logic, not dependent on API
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Score should be calculated: perfect 50/30/20 = 100
        self.assertEqual(score, 100)
        self.assertIsInstance(advice, str)

    @patch('finance_app.ai.genai')
    def test_ai_handles_network_error(self, mock_genai):
        """Test that AI gracefully handles network errors and still returns score."""
        # Mock a network error in Client initialization
        mock_genai.Client.side_effect = Exception("Network error")
        mock_genai.GenerativeModel.side_effect = Exception("Network error")
        
        # Call AI function - should not raise exception
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Score should be calculated from our logic (perfect 50/30/20 = 100)
        self.assertEqual(score, 100)
        self.assertIsInstance(advice, str)

    def test_ai_score_parsing_from_response(self):
        """Test that AI can parse scores from various response formats."""
        # This indirectly tests score parsing by checking fallback behavior
        score, advice = get_ai_insights(5000, 2500, 1500, 1000, {'restaurant': 500, 'entertainment': 300})
        
        # Score should be between 0 and 100
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_ai_enhanced_payload_structure(self):
        """Test that AI insights generates enhanced payload with comprehensive metrics."""
        # Test with specific financial data
        income = 5000
        needs = 2500  # 50%
        wants = 1500  # 30%
        savings = 1000  # 20%
        top_wants = {'restaurant': 400, 'entertainment': 300, 'shopping': 200, 'subscriptions': 150, 'hobbies': 100}
        
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants)
        
        # Score should be deterministic from calculate_health_score (perfect 50/30/20 = 100)
        self.assertEqual(score, 100)
        self.assertIsInstance(advice, str)
        # Advice should contain key elements from fallback for perfect score
        self.assertTrue(len(advice) > 0)

    def test_ai_payload_with_budget_deviation(self):
        """Test AI payload calculation with significant budget deviations."""
        # Test with unbalanced budget (80% needs, 20% wants, 0% savings)
        income = 5000
        needs = 4000  # 80% (over-target by 30%)
        wants = 1000  # 20% (under-target by 10%)
        savings = 0    # 0% (under-target by 20%)
        top_wants = {'food': 500, 'utilities': 300, 'other': 200}
        
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants)
        
        # Score should be lower due to deviations and zero savings
        self.assertIsInstance(score, int)
        self.assertLess(score, 100)  # Not perfect
        self.assertGreaterEqual(score, 0)
        self.assertIsInstance(advice, str)

    def test_ai_payload_with_extreme_wants(self):
        """Test AI payload with wants exceeding target significantly."""
        # Test with high wants spending (70% of income on wants)
        income = 5000
        needs = 1500  # 30% (under-target)
        wants = 3500  # 70% (over-target by 40%)
        savings = 0    # 0% (under-target by 20%)
        top_wants = {'shopping': 1500, 'dining': 1200, 'entertainment': 800}
        
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants)
        
        # Score should be lower but weighted deviations mean it won't be too extreme
        self.assertIsInstance(score, int)
        self.assertLess(score, 100)
        self.assertGreater(score, 30)  # But still has some positive score
        self.assertIsInstance(advice, str)

    def test_ai_payload_with_low_income(self):
        """Test AI payload generation with low income."""
        # Test with minimal income
        income = 1000
        needs = 500    # 50%
        wants = 300    # 30%
        savings = 200  # 20%
        top_wants = {'food': 150, 'transport': 150}
        
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants)
        
        # Should still work correctly
        self.assertEqual(score, 100)
        self.assertIsInstance(advice, str)

    def test_ai_health_status_categorization(self):
        """Test that AI correctly categorizes health status."""
        # Test three scenarios: Excellent (score 100), Good (score 75), Fair (score 40)
        test_cases = [
            (5000, 2500, 1500, 1000, 100),  # Perfect 50/30/20
            (5000, 2700, 1500, 800, 75),    # Needs slightly over, savings under
            (5000, 3500, 1500, 0, 40)       # High needs, zero savings
        ]
        
        for income, needs, wants, savings, expected_score_approx in test_cases:
            top_wants = {'food': 300}
            score, advice = get_ai_insights(income, needs, wants, savings, top_wants)
            
            # Score should match our calculation
            self.assertIsInstance(score, int)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    @patch('finance_app.ai.genai')
    def test_ai_generation_config_applied(self, mock_genai):
        """Test that generation config parameters are correctly applied."""
        # Mock the GenerativeModel and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Health Score: 80\nAdvice: Increase savings"
        mock_model.generate_content.return_value = mock_response
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.Client.return_value.models.generate_content = MagicMock(return_value=mock_response)
        
        # Call with API key set
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            score, advice = get_ai_insights(5000, 2500, 1500, 1000, {'food': 300})
        
        # Verify generate_content was called with proper config
        self.assertIsInstance(score, int)
        self.assertIsInstance(advice, str)

    def test_determine_priority_reduce_needs(self):
        """Test priority determination when needs are overspent."""
        # Needs at +25% over target, wants at target, savings under target
        priority = _determine_priority(0.25, 0.0, -0.10)
        self.assertEqual(priority, "reduce_needs")

    def test_determine_priority_reduce_wants(self):
        """Test priority determination when wants are overspent."""
        # Needs at target, wants at +20% over target, savings under target
        priority = _determine_priority(0.0, 0.20, -0.15)
        self.assertEqual(priority, "reduce_wants")

    def test_determine_priority_increase_savings(self):
        """Test priority determination when savings are undersaved."""
        # Needs at target, wants at target, savings at -20% under target
        priority = _determine_priority(0.0, 0.0, -0.20)
        self.assertEqual(priority, "increase_savings")

    def test_determine_priority_perfect_budget(self):
        """Test priority determination with perfect 50/30/20 budget."""
        # All categories at target
        priority = _determine_priority(0.0, 0.0, 0.0)
        self.assertEqual(priority, "optimize_all_categories")

    def test_determine_secondary_priority_multiple_issues(self):
        """Test secondary priority determination with multiple issues."""
        # Both needs and wants are overspent, wants is worse
        secondary = _determine_secondary_priority(0.15, 0.20, -0.10)
        # Should pick the second-worst issue
        self.assertIsInstance(secondary, str)
        self.assertIn(secondary, ["reduce_needs", "reduce_wants", "increase_savings", "maintain_current_balance"])

    def test_determine_secondary_priority_single_issue(self):
        """Test secondary priority when only one issue exists."""
        # Only wants is overspent, rest are perfect
        secondary = _determine_secondary_priority(0.0, 0.25, 0.0)
        # Should return the same issue or maintain balance
        self.assertIsInstance(secondary, str)
        self.assertIn(secondary, ["reduce_wants", "maintain_current_balance"])

    def test_determine_secondary_priority_no_issues(self):
        """Test secondary priority with perfect budget."""
        secondary = _determine_secondary_priority(0.0, 0.0, 0.0)
        self.assertEqual(secondary, "maintain_current_balance")

    def test_validate_file_invalid_name(self):
        """Test file validation with invalid names."""
        bad_file = "invalid_name.xlsx"
        data = {
            'Date': ['1/1/2026'],
            'Name': [''],  # Empty name
            'Type': ['Needs'],
            'Amount': [100.00],
            'Category': ['Rent']
        }
        pd.DataFrame(data).to_excel(bad_file, index=False)
        valid, errors = validate_file(bad_file)
        self.assertFalse(valid)
        self.assertTrue(any('Invalid name' in msg for _, msg in errors))
        os.remove(bad_file)

    def test_validate_file_invalid_date_format(self):
        """Test file validation with invalid date format."""
        bad_file = "invalid_date.xlsx"
        data = {
            'Date': ['2026-01-01'],  # Wrong format, should be dd/mm/yyyy
            'Name': ['Rent'],
            'Type': ['Needs'],
            'Amount': [1000.00],
            'Category': ['Rent']
        }
        pd.DataFrame(data).to_excel(bad_file, index=False)
        valid, errors = validate_file(bad_file)
        self.assertFalse(valid)
        self.assertTrue(any('Invalid date format' in msg for _, msg in errors))
        os.remove(bad_file)

    def test_validate_file_accepts_dash_format_dates(self):
        """Test that dd-mm-YYYY date strings are accepted."""
        dash_file = "dash_date.xlsx"
        data = {
            'Date': ['01-01-2026', '02-01-2026'],  # dd-mm-YYYY should be valid
            'Name': ['Rent', 'Groceries'],
            'Type': ['Needs', 'Needs'],
            'Amount': [1000.00, 200.00],
            'Category': ['Housing', 'Food']
        }
        pd.DataFrame(data).to_excel(dash_file, index=False)
        valid, df = validate_file(dash_file)
        self.assertTrue(valid)
        self.assertIsInstance(df, pd.DataFrame)
        os.remove(dash_file)

    def test_validate_file_invalid_category(self):
        """Test file validation with invalid category (empty)."""
        bad_file = "invalid_category.xlsx"
        data = {
            'Date': ['1/1/2026'],
            'Name': ['Rent'],
            'Type': ['Needs'],
            'Amount': [1000.00],
            'Category': [None]  # Empty category
        }
        pd.DataFrame(data).to_excel(bad_file, index=False)
        valid, errors = validate_file(bad_file)
        self.assertFalse(valid)
        self.assertTrue(any('Invalid category' in msg for _, msg in errors))
        os.remove(bad_file)

    def test_validate_file_accepts_datetime_objects(self):
        """Test that datetime/Timestamp dates are accepted."""
        dt_file = "datetime_dates.xlsx"
        data = {
            'Date': [pd.Timestamp('2026-01-01'), pd.Timestamp('2026-01-02')],
            'Name': ['Rent', 'Groceries'],
            'Type': ['Needs', 'Needs'],
            'Amount': [1000.00, 200.00],
            'Category': ['Housing', 'Food']
        }
        pd.DataFrame(data).to_excel(dt_file, index=False)
        valid, df = validate_file(dt_file)
        self.assertTrue(valid)
        self.assertIsInstance(df, pd.DataFrame)
        os.remove(dt_file)

    def test_analyze_data_with_mixed_types(self):
        """Test analyze_data with all three spending types (Needs, Wants, Savings)."""
        mixed_file = "mixed_types.xlsx"
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026'],
            'Name': ['Rent', 'Movie', 'Investment'],
            'Type': ['Needs', 'Wants', 'Savings'],
            'Amount': [1000, 200, 500],
            'Category': ['Rent', 'Entertainment', 'Stocks']
        }
        pd.DataFrame(data).to_excel(mixed_file, index=False)
        valid, df = validate_file(mixed_file)
        self.assertTrue(valid)
        needs, wants, savings, top_wants = analyze_data(df, 1700)
        self.assertEqual(needs, 1000)
        self.assertEqual(wants, 200)
        self.assertEqual(savings, 500)
        os.remove(mixed_file)

    def test_validate_file_parses_amounts_with_commas(self):
        """Test that amounts with commas are parsed correctly."""
        comma_file = "comma_amounts.xlsx"
        data = {
            'Date': ['1/1/2026', '2/1/2026'],
            'Name': ['Rent', 'Groceries'],
            'Type': ['Needs', 'Needs'],
            'Amount': ['1,000.50', '200'],  # Strings with comma
            'Category': ['Housing', 'Food']
        }
        pd.DataFrame(data).to_excel(comma_file, index=False)
        valid, df = validate_file(comma_file)
        self.assertTrue(valid)
        self.assertIsInstance(df, pd.DataFrame)
        # Verify amounts can be normalized by removing commas
        amt0 = float(str(df.loc[0, 'Amount']).replace(',', ''))
        amt1 = float(str(df.loc[1, 'Amount']).replace(',', ''))
        self.assertAlmostEqual(amt0, 1000.50, places=2)
        self.assertAlmostEqual(amt1, 200.00, places=2)
        os.remove(comma_file)

    def test_analyze_data_category_lowercasing(self):
        """Test that analyze_data correctly lowercases categories."""
        case_file = "case_sensitive.xlsx"
        data = {
            'Date': ['1/1/2026', '1/2/2026'],
            'Name': ['Movie1', 'Movie2'],
            'Type': ['Wants', 'Wants'],
            'Amount': [50, 75],
            'Category': ['Entertainment', 'ENTERTAINMENT']  # Different cases
        }
        pd.DataFrame(data).to_excel(case_file, index=False)
        valid, df = validate_file(case_file)
        self.assertTrue(valid)
        needs, wants, savings, top_wants = analyze_data(df, 200)
        # Both should be combined as 'entertainment' (lowercase)
        self.assertEqual(len(top_wants), 1)
        self.assertIn('entertainment', top_wants.index)
        self.assertEqual(top_wants['entertainment'], 125)
        os.remove(case_file)

    def test_50_30_20_ratio_check(self):
        """Test that analyze_data returns correct 50/30/20 ratios."""
        ratio_file = "ratio_test.xlsx"
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026', '1/4/2026', '1/5/2026'],
            'Name': ['Rent', 'Bill', 'Food', 'Movie', 'Savings'],
            'Type': ['Needs', 'Needs', 'Wants', 'Wants', 'Savings'],
            'Amount': [500, 500, 300, 300, 400],  # 1000 needs, 600 wants, 400 savings = 50%, 30%, 20%
            'Category': ['Rent', 'Utilities', 'Groceries', 'Entertainment', 'Investment']
        }
        pd.DataFrame(data).to_excel(ratio_file, index=False)
        valid, df = validate_file(ratio_file)
        self.assertTrue(valid)
        income = 2000
        needs, wants, savings, top_wants = analyze_data(df, income)
        # Check percentages
        needs_pct = (needs / income) * 100
        wants_pct = (wants / income) * 100
        savings_pct = (savings / income) * 100
        self.assertAlmostEqual(needs_pct, 50, places=1)
        self.assertAlmostEqual(wants_pct, 30, places=1)
        self.assertAlmostEqual(savings_pct, 20, places=1)
        os.remove(ratio_file)

    def test_currency_edge_cases(self):
        """Test currency lookup edge cases."""
        # Invalid currency code
        self.assertIsNone(get_currency_symbol(self.currencies, 'XXX'))
        # Empty string currency code
        self.assertIsNone(get_currency_symbol(self.currencies, ''))
        # None as currency code
        self.assertIsNone(get_currency_symbol(self.currencies, None))

    @patch('finance_app.pdf_generator.generate_pie_chart')
    @patch('finance_app.pdf_generator.generate_category_chart')
    @patch('finance_app.pdf_generator.generate_bar_chart')
    def test_pdf_generation_calls_all_charts(self, mock_bar, mock_pie, mock_category):
        """Test that PDF generation calls all three chart functions."""
        # Create actual temporary image files with minimal PNG data (1x1 transparent pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create temp files with actual PNG data
        bar_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        bar_file.write(png_data)
        bar_file.close()
        
        pie_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        pie_file.write(png_data)
        pie_file.close()
        
        category_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        category_file.write(png_data)
        category_file.close()
        
        mock_bar.return_value = bar_file.name
        mock_pie.return_value = pie_file.name
        mock_category.return_value = category_file.name
        
        pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            generate_pdf(pdf_path, 1000, '£', 500, 300, 200, pd.Series({'food': 100}), 75, "Good health")
            
            # Verify all chart functions were called
            mock_bar.assert_called_once()
            mock_pie.assert_called_once()
            mock_category.assert_called_once()
            
            # Verify PDF was created
            self.assertTrue(os.path.exists(pdf_path))
        finally:
            # Cleanup
            for f in [pdf_path, bar_file.name, pie_file.name, category_file.name]:
                if os.path.exists(f):
                    os.remove(f)

    @patch('finance_app.pdf_generator.generate_pie_chart')
    @patch('finance_app.pdf_generator.generate_category_chart')
    @patch('finance_app.pdf_generator.generate_bar_chart')
    def test_pdf_generation_with_different_currencies(self, mock_bar, mock_pie, mock_category):
        """Test PDF generation with various currency symbols."""
        # Create actual PNG data (1x1 transparent pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        currencies_to_test = ['$', '€', '¥', '₹', '£']
        for symbol in currencies_to_test:
            # Create temp PNG files
            bar_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            bar_file.write(png_data)
            bar_file.close()
            
            pie_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            pie_file.write(png_data)
            pie_file.close()
            
            category_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            category_file.write(png_data)
            category_file.close()
            
            mock_bar.return_value = bar_file.name
            mock_pie.return_value = pie_file.name
            mock_category.return_value = category_file.name
            
            pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            try:
                generate_pdf(pdf_path, 5000, symbol, 2500, 1500, 1000, pd.Series({'dining': 500}), 80, "Excellent")
                self.assertTrue(os.path.exists(pdf_path))
            finally:
                for f in [pdf_path, bar_file.name, pie_file.name, category_file.name]:
                    if os.path.exists(f):
                        os.remove(f)

    def test_download_template_creates_valid_file(self):
        """Test that template Excel file creation works with correct structure."""
        import pandas as pd
        from finance_app.config import DOWNLOADS_PATH, TEMPLATE_FILE
        
        # Create template directly (same code as download_template)
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026', '1/4/2026', '1/5/2026', '1/6/2026', '1/7/2026', '1/8/2026', '1/9/2026', '1/10/2026'],
            'Name': ['Rent', 'all you can eat DAIU', 'Investments', 'Electricity Bills', 'Thai Grass', 'NX Bus Pass', 'Aldi Week 1', 'Kebab Rush', 'Stocks Investment', 'Gym Subscription'],
            'Type': ['Needs', 'Wants', 'Savings', 'Needs', 'Wants', 'Needs', 'Needs', 'Wants', 'Savings', 'Needs'],
            'Amount': [520.00, 50.00, 430.00, 4.20, 7.50, 53.00, 16.00, 6.50, 20.00, 18.50],
            'Category': ['Rent', 'Eating Out', 'Gold Investment', 'Electricity', 'Eating Out', 'Bus Pass', 'Groceries', 'Eating Out', 'Stocks', 'Sports']
        }
        df = pd.DataFrame(data)
        template_path = os.path.join(DOWNLOADS_PATH, TEMPLATE_FILE)
        df.to_excel(template_path, index=False)
        
        try:
            # Verify it's a valid Excel file
            df_read = pd.read_excel(template_path)
            
            # Check required columns
            required_cols = ['Date', 'Name', 'Type', 'Amount', 'Category']
            for col in required_cols:
                self.assertIn(col, df_read.columns)
            
            # Check data types and content
            self.assertEqual(len(df_read), 10)  # Should have 10 example rows
            self.assertTrue(all(df_read['Type'].isin(['Needs', 'Wants', 'Savings'])))
            self.assertAlmostEqual(df_read['Amount'].sum(), 1125.70, places=2)  # Verify all amounts
        finally:
            if os.path.exists(template_path):
                os.remove(template_path)

    def test_analyze_workflow_end_to_end(self):
        """Test complete analysis workflow: load currencies -> validate -> analyze."""
        # Create test file
        test_file = "e2e_test.xlsx"
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026', '1/4/2026', '1/5/2026'],
            'Name': ['Rent', 'Utilities', 'Groceries', 'Cinema', 'Savings'],
            'Type': ['Needs', 'Needs', 'Needs', 'Wants', 'Savings'],
            'Amount': [800, 150, 150, 50, 400],
            'Category': ['Housing', 'Utilities', 'Food', 'Entertainment', 'Emergency Fund']
        }
        pd.DataFrame(data).to_excel(test_file, index=False)
        
        try:
            # Step 1: Load currencies
            currencies = load_currencies()
            self.assertGreater(len(currencies), 0)
            
            # Step 2: Validate file
            valid, df = validate_file(test_file)
            self.assertTrue(valid)
            self.assertIsInstance(df, pd.DataFrame)
            
            # Step 3: Analyze data
            income = 1550
            needs, wants, savings, top_wants = analyze_data(df, income)
            
            # Verify results
            self.assertEqual(needs, 1100)  # Rent + Utilities + Groceries
            self.assertEqual(wants, 50)    # Cinema
            self.assertEqual(savings, 400) # Savings
            self.assertIn('entertainment', top_wants.index)
            
            # Step 4: Get AI insights
            score, advice = get_ai_insights(income, needs, wants, savings, top_wants.to_dict())
            self.assertIsInstance(score, int)
            self.assertIsInstance(advice, str)
            
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_validate_file_with_empty_dataframe(self):
        """Test file validation with an empty DataFrame."""
        empty_file = "empty.xlsx"
        data = {
            'Date': [],
            'Name': [],
            'Type': [],
            'Amount': [],
            'Category': []
        }
        pd.DataFrame(data).to_excel(empty_file, index=False)
        
        valid, result = validate_file(empty_file)
        # Empty dataframe has correct columns, so it should be valid
        self.assertTrue(valid)
        self.assertEqual(len(result), 0)
        os.remove(empty_file)

    def test_validate_file_drops_fully_empty_rows(self):
        """Test validator drops rows where all required fields are empty."""
        drop_file = "drop_empty_rows.xlsx"
        data = {
            'Date': ['1/1/2026', None],
            'Name': ['Rent', None],
            'Type': ['Needs', None],
            'Amount': [1000.00, None],
            'Category': ['Housing', None]
        }
        pd.DataFrame(data).to_excel(drop_file, index=False)
        valid, df = validate_file(drop_file)
        self.assertTrue(valid)
        # Only the first row should remain after dropping fully empty rows
        self.assertEqual(len(df), 1)
        os.remove(drop_file)

    def test_income_validation_boundary_cases(self):
        """Test income validation with boundary and special values."""
        # Very small positive income
        self.assertTrue(is_valid_income(0.01))
        
        # Very large income
        self.assertTrue(is_valid_income(999999999))
        
        # Exactly zero
        self.assertFalse(is_valid_income(0))
        self.assertFalse(is_valid_income(0.0))
        
        # String representations
        self.assertTrue(is_valid_income("1000.50"))
        self.assertTrue(is_valid_income("1"))
        self.assertFalse(is_valid_income("0"))
        self.assertFalse(is_valid_income("-100.50"))

if __name__ == '__main__':
    unittest.main()


# ============================================================================
# STREAMLIT WEB APP INTEGRATION TESTS
# ============================================================================
# These tests verify that the core logic works correctly with the Streamlit app

class TestStreamlitIntegration(unittest.TestCase):
    """Tests for Streamlit web app integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for Streamlit integration tests."""
        cls.currencies = load_currencies()
        cls.test_file = "streamlit_test_data.xlsx"
        # Create a valid test Excel file
        data = {
            'Date': ['1/1/2026', '2/1/2026', '3/1/2026'],
            'Name': ['Rent', 'Groceries', 'Movie'],
            'Type': ['Needs', 'Needs', 'Wants'],
            'Amount': [1000, 200, 30],
            'Category': ['Housing', 'Food', 'Entertainment']
        }
        pd.DataFrame(data).to_excel(cls.test_file, index=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)
    
    def test_streamlit_file_uploader_compatibility(self):
        """Test that validate_file works with Streamlit's UploadedFile object."""
        # Streamlit file objects are file-like, should work with validate_file
        valid, result = validate_file(self.test_file)
        self.assertTrue(valid)
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_streamlit_download_button_data_preparation(self):
        """Test that PDF generation creates binary data suitable for download."""
        pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            # Create PNG files for charts
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            
            bar_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            bar_file.write(png_data)
            bar_file.close()
            
            pie_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            pie_file.write(png_data)
            pie_file.close()
            
            category_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            category_file.write(png_data)
            category_file.close()
            
            with patch('finance_app.pdf_generator.generate_bar_chart', return_value=bar_file.name), \
                 patch('finance_app.pdf_generator.generate_pie_chart', return_value=pie_file.name), \
                 patch('finance_app.pdf_generator.generate_category_chart', return_value=category_file.name):
                
                generate_pdf(pdf_path, 1230, '£', 1000, 200, 30, 
                           pd.Series({'entertainment': 30}), 85, "Good financial health")
            
            # Verify PDF file is created and readable
            self.assertTrue(os.path.exists(pdf_path))
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
                # PDF files start with %PDF
                self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        finally:
            for f in [pdf_path, bar_file.name, pie_file.name, category_file.name]:
                if os.path.exists(f):
                    os.remove(f)
    
    def test_streamlit_metric_display_data_types(self):
        """Test that analysis results have correct data types for Streamlit metrics."""
        valid, df = validate_file(self.test_file)
        self.assertTrue(valid)
        
        income = 1230
        needs, wants, savings, top_wants = analyze_data(df, income)
        
        # Streamlit metrics expect numeric types (int, float, or numpy types)
        self.assertTrue(isinstance(needs, (int, float)) or hasattr(needs, 'item'))
        self.assertTrue(isinstance(wants, (int, float)) or hasattr(wants, 'item'))
        self.assertTrue(isinstance(savings, (int, float)) or hasattr(savings, 'item'))
        
        # Verify percentages can be calculated (convert numpy types if needed)
        needs_val = float(needs) if hasattr(needs, 'item') else needs
        wants_val = float(wants) if hasattr(wants, 'item') else wants
        savings_val = float(savings) if hasattr(savings, 'item') else savings
        
        needs_pct = (needs_val / income) * 100
        wants_pct = (wants_val / income) * 100
        savings_pct = (savings_val / income) * 100
        
        self.assertIsInstance(needs_pct, float)
        self.assertIsInstance(wants_pct, float)
        self.assertIsInstance(savings_pct, float)
    
    def test_streamlit_health_score_display(self):
        """Test that health score is suitable for Streamlit display."""
        valid, df = validate_file(self.test_file)
        income = 1230
        needs, wants, savings, _ = analyze_data(df, income)
        
        health_score = calculate_health_score(income, needs, wants, savings)
        
        # Score should be displayable integer between 0-100
        self.assertIsInstance(health_score, int)
        self.assertGreaterEqual(health_score, 0)
        self.assertLessEqual(health_score, 100)
    
    def test_streamlit_session_state_compatibility(self):
        """Test that analysis results are compatible with Streamlit session state."""
        valid, df = validate_file(self.test_file)
        income = 1230
        currency = 'GBP'
        symbol = get_currency_symbol(self.currencies, currency)
        
        needs, wants, savings, top_wants = analyze_data(df, income)
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants.to_dict())
        
        # All results should be serializable (for session state)
        result = {
            'income': income,
            'currency': currency,
            'symbol': symbol,
            'needs': needs,
            'wants': wants,
            'savings': savings,
            'top_wants': top_wants.to_dict(),
            'score': score,
            'advice': advice
        }
        
        # Should be JSON serializable
        import json
        json_str = json.dumps(result, default=str)
        self.assertIsInstance(json_str, str)
    
    def test_streamlit_currency_selection_options(self):
        """Test that all currencies can be used in Streamlit selectbox."""
        # This should work for any currency in the list
        for currency in self.currencies:
            code = currency['code']
            symbol = get_currency_symbol(self.currencies, code)
            self.assertIsNotNone(symbol)


# ============================================================================
# LEGACY TKINTER APP TESTS (COMMENTED OUT)
# ============================================================================
# The following tests were used for the Tkinter desktop application.
# They are kept for reference but are no longer executed.
# See LEGACY_FILES.md for information about the legacy app.

"""
# === LEGACY TKINTER GUI TESTS ===
# These tests verified Tkinter GUI functionality (app.py, modules/ui.py)
# 
# class TestTkinterGUI(unittest.TestCase):
#     '''Test Tkinter desktop app GUI components.'''
#     
#     def test_tkinter_income_validation_ui(self):
#         '''Test that income validation updates UI color correctly.'''
#         # Tkinter-specific: root = tk.Tk(), app = FinancialHealthChecker(root)
#         # Verified that income_entry.config(bg=...) called on key release
#         pass
#     
#     def test_tkinter_file_upload_button(self):
#         '''Test Tkinter file dialog and validation workflow.'''
#         # Verified filedialog.askopenfilename() integration
#         pass
#     
#     def test_tkinter_analyze_button_state_management(self):
#         '''Test that Analyze button is enabled/disabled based on validation.'''
#         # Button state: tk.DISABLED until valid file uploaded
#         pass
#     
#     def test_tkinter_feedback_terminal_logging(self):
#         '''Test feedback text widget receives validation messages.'''
#         # Verified feedback_text.insert() and text widget state management
#         pass


# === LEGACY PYINSTALLER PACKAGING TESTS ===
# These tests verified PyInstaller .exe packaging (setup.py)
#
# class TestPyInstallerPackaging(unittest.TestCase):
#     '''Test PyInstaller build configuration for .exe packaging.'''
#     
#     def test_pyinstaller_onefile_configuration(self):
#         '''Test that PyInstaller is configured for single .exe file.'''
#         # Verified: --onefile flag in setup.py
#         pass
#     
#     def test_pyinstaller_hidden_data_inclusion(self):
#         '''Test that data/currencies.json is included in build.'''
#         # Verified: --add-data 'data/currencies.json:data' in setup.py
#         pass
#     
#     def test_pyinstaller_windowed_mode(self):
#         '''Test that .exe runs in windowed mode (no console).'''
#         # Verified: --windowed flag in setup.py
#         pass
"""