
import unittest
import os
import json
import pandas as pd
from modules.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data
from modules.ai import get_ai_insights

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

if __name__ == '__main__':
    unittest.main()