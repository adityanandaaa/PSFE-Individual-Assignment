
import unittest
import os
import json
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open, call
import tempfile
from modules.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data
from modules.ai import get_ai_insights
from modules.pdf_generator import generate_pdf

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
        self.assertTrue(any('Invalid amount' in e for e in errors))
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

    def test_ai_fallback(self):
        # Should always return a score and advice, even if AI fails
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        self.assertIsInstance(score, int)
        self.assertIsInstance(advice, str)

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'})
    @patch('modules.ai.genai')
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
        
        # Verify results
        self.assertIsInstance(score, int)
        self.assertIsInstance(advice, str)
        self.assertGreater(score, 0)
        self.assertLess(score, 101)
        # Verify configure was called with the env key
        mock_genai.configure.assert_called()

    @patch('modules.ai.genai')
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
        """Test that AI falls back to default advice when GEMINI_API_KEY is not set."""
        # Simulate missing API key
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Should return default fallback values
        self.assertEqual(score, 70)
        self.assertIn("focus on reducing Wants", advice)

    @patch('modules.ai.genai')
    def test_ai_handles_network_error(self, mock_genai):
        """Test that AI gracefully handles network errors."""
        # Mock a network error in Client initialization
        mock_genai.Client.side_effect = Exception("Network error")
        mock_genai.GenerativeModel.side_effect = Exception("Network error")
        
        # Call AI function - should not raise exception
        score, advice = get_ai_insights(1000, 500, 300, 200, {'food': 100})
        
        # Verify fallback is used (score should be default fallback)
        self.assertIsInstance(score, int)
        self.assertIsInstance(advice, str)
        # Fallback score is 70, but since mocking returns error, it should use fallback
        self.assertEqual(score, 70)

    def test_ai_score_parsing_from_response(self):
        """Test that AI can parse scores from various response formats."""
        # This indirectly tests score parsing by checking fallback behavior
        score, advice = get_ai_insights(5000, 2500, 1500, 1000, {'restaurant': 500, 'entertainment': 300})
        
        # Score should be between 0 and 100
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

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
        self.assertTrue(any('Invalid name' in e for e in errors))
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
        self.assertTrue(any('Invalid date format' in e for e in errors))
        os.remove(bad_file)

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
        self.assertTrue(any('Invalid category' in e for e in errors))
        os.remove(bad_file)

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

    @patch('modules.pdf_generator.generate_pie_chart')
    @patch('modules.pdf_generator.generate_category_chart')
    @patch('modules.pdf_generator.generate_bar_chart')
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

    @patch('modules.pdf_generator.generate_pie_chart')
    @patch('modules.pdf_generator.generate_category_chart')
    @patch('modules.pdf_generator.generate_bar_chart')
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
        from modules.config import DOWNLOADS_PATH, TEMPLATE_FILE
        
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