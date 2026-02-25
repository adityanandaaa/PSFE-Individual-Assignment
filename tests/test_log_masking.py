import logging
import unittest
from io import StringIO
from src.finance_app.log_masker import SensitiveDataFilter


class TestLogMasking(unittest.TestCase):
    def setUp(self):
        # Create a dedicated logger for testing
        self.logger = logging.getLogger('test_masking')
        self.logger.setLevel(logging.DEBUG)
        
        # Capture logs in a string buffer
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(self.handler)
        
        # Add the masking filter
        self.filter = SensitiveDataFilter()
        self.logger.addFilter(self.filter)

    def tearDown(self):
        # Clean up handlers to avoid interference
        self.logger.removeHandler(self.handler)
        self.logger.removeFilter(self.filter)

    def get_logs(self):
        return self.log_capture.getvalue()

    def test_currency_masking_usd(self):
        self.logger.info("The balance is $1,234.56 today.")
        self.assertIn("The balance is $***", self.get_logs())
        self.assertNotIn("1,234.56", self.get_logs())

    def test_currency_masking_gbp(self):
        self.logger.info("Spent £500 on rent.")
        self.assertIn("Spent £***", self.get_logs())
        self.assertNotIn("500", self.get_logs())

    def test_currency_masking_eur(self):
        self.logger.info("Transfer €10.00 to savings.")
        self.assertIn("Transfer €***", self.get_logs())
        self.assertNotIn("10.00", self.get_logs())

    def test_api_key_masking(self):
        # Simulate an accidental leak of a Gemini-style API key
        fake_key = "AIzaSyAzX-1234567890abcdefghijklmnopq"
        self.logger.info(f"Using key: {fake_key}")
        self.assertIn("Using key: AIzaSy***", self.get_logs())
        self.assertNotIn("AzX-123", self.get_logs())

    def test_large_digit_sequence_masking(self):
        # 10 or more digits (common for account numbers)
        account_num = "1234567890123"
        self.logger.info(f"Account: {account_num}")
        self.assertIn("Account: ***", self.get_logs())
        self.assertNotIn(account_num, self.get_logs())

    def test_masking_with_args(self):
        # Test that arguments passed to logger are also masked
        self.logger.info("Transaction for %s amount: %s", "User1", "$150.00")
        logs = self.get_logs()
        self.assertIn("Transaction for User1 amount: $***", logs)
        self.assertNotIn("150.00", logs)

    def test_non_sensitive_data_not_masked(self):
        msg = "Successfully processed 5 items."
        self.logger.info(msg)
        self.assertIn(msg, self.get_logs())


if __name__ == '__main__':
    unittest.main()
