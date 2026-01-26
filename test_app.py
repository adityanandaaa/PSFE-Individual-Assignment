import unittest
import json
import os

class TestFinancialHealthChecker(unittest.TestCase):

    def setUp(self):
        # Load currencies for testing
        with open('currencies.json', 'r') as f:
            self.currencies = json.load(f)

    def test_load_currencies(self):
        # Test that currencies.json is loaded correctly
        self.assertIsInstance(self.currencies, list)
        self.assertGreater(len(self.currencies), 0)
        # Check for GBP as default
        gbp = next((c for c in self.currencies if c['code'] == 'GBP'), None)
        self.assertIsNotNone(gbp)
        self.assertEqual(gbp['symbol'], '£')

    def test_income_validation_positive(self):
        # Test income validation: positive numbers > 0
        self.assertTrue(self._is_valid_income(1000))
        self.assertTrue(self._is_valid_income(100.50))

    def test_income_validation_invalid(self):
        # Test invalid incomes
        self.assertFalse(self._is_valid_income(0))
        self.assertFalse(self._is_valid_income(-100))
        self.assertFalse(self._is_valid_income('abc'))
        self.assertFalse(self._is_valid_income(None))

    def test_currency_selection(self):
        # Test currency selection logic
        selected = self._get_currency_symbol('GBP')
        self.assertEqual(selected, '£')
        selected = self._get_currency_symbol('USD')
        self.assertEqual(selected, '$')
        selected = self._get_currency_symbol('INVALID')
        self.assertIsNone(selected)

    # Helper methods (to be implemented in main code)
    def _is_valid_income(self, income):
        try:
            val = float(income)
            return val > 0
        except (ValueError, TypeError):
            return False

    def _get_currency_symbol(self, code):
        currency = next((c for c in self.currencies if c['code'] == code), None)
        return currency['symbol'] if currency else None

if __name__ == '__main__':
    unittest.main()