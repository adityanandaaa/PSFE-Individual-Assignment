"""Tests for input sanitization module.

Validates that all sanitization functions properly remove XSS/injection
patterns while preserving legitimate data.
"""

import unittest
from finance_app.sanitizer import (
    sanitize_text,
    sanitize_filename,
    sanitize_category,
    sanitize_currency_symbol,
    sanitize_amount,
    sanitize_dict_values,
    is_safe_to_display
)


class TestInputSanitization(unittest.TestCase):
    """Test suite for input sanitization functions."""
    
    # === SANITIZE TEXT TESTS ===
    
    def test_sanitize_text_removes_html_tags(self):
        """Test that sanitize_text removes HTML tags."""
        dangerous = "<script>alert('XSS')</script>Hello"
        result = sanitize_text(dangerous)
        self.assertNotIn('<script>', result)
        # Script tags are removed, but inner text content may remain (and is safe because no scripts execute)
        self.assertIn('Hello', result)
    
    def test_sanitize_text_escapes_html_entities(self):
        """Test that sanitize_text escapes HTML entities."""
        dangerous = "Test & <tag> && \"quotes\""
        result = sanitize_text(dangerous)
        # Should contain HTML-escaped versions
        self.assertIn('&amp;', result)
        self.assertNotIn('<tag>', result)
    
    def test_sanitize_text_removes_javascript(self):
        """Test that sanitize_text removes JavaScript."""
        dangerous = "Category<img src=x onerror='alert(1)'>"
        result = sanitize_text(dangerous)
        self.assertNotIn('onerror', result)
        self.assertNotIn('<img', result)
    
    def test_sanitize_text_respects_max_length(self):
        """Test that sanitize_text enforces max length."""
        long_text = "A" * 200
        result = sanitize_text(long_text, max_length=150)
        self.assertLessEqual(len(result), 150)
    
    def test_sanitize_text_preserves_safe_input(self):
        """Test that sanitize_text preserves safe text."""
        safe = "Groceries & Entertainment"
        result = sanitize_text(safe)
        self.assertIn("Groceries", result)
        self.assertIn("Entertainment", result)
    
    def test_sanitize_text_handles_none(self):
        """Test that sanitize_text handles None input."""
        result = sanitize_text(None)
        self.assertEqual(result, "")
    
    # === SANITIZE FILENAME TESTS ===
    
    def test_sanitize_filename_removes_path_traversal(self):
        """Test that sanitize_filename removes path traversal attempts."""
        malicious = "../../../etc/passwd"
        result = sanitize_filename(malicious)
        self.assertNotIn('..', result)
        self.assertNotIn('/', result)
    
    def test_sanitize_filename_removes_backslashes(self):
        """Test that sanitize_filename removes Windows path separators."""
        malicious = "..\\..\\windows\\system32"
        result = sanitize_filename(malicious)
        self.assertNotIn('\\', result)
    
    def test_sanitize_filename_removes_dots(self):
        """Test that sanitize_filename removes dangerous dots."""
        malicious = "file...exe"
        result = sanitize_filename(malicious)
        # Dots are removed
        self.assertNotIn('...', result)
    
    def test_sanitize_filename_handles_html_in_name(self):
        """Test that sanitize_filename handles HTML in filenames."""
        dangerous = "report<script>.pdf"
        result = sanitize_filename(dangerous)
        self.assertNotIn('<script>', result)
    
    def test_sanitize_filename_respects_max_length(self):
        """Test that sanitize_filename enforces max length."""
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=255)
        self.assertLessEqual(len(result), 255)
    
    def test_sanitize_filename_handles_empty(self):
        """Test that sanitize_filename handles empty input."""
        result = sanitize_filename("")
        self.assertEqual(result, "file")
    
    def test_sanitize_filename_handles_none(self):
        """Test that sanitize_filename handles None input."""
        result = sanitize_filename(None)
        self.assertEqual(result, "file")
    
    # === SANITIZE CATEGORY TESTS ===
    
    def test_sanitize_category_removes_injections(self):
        """Test that sanitize_category removes injection attempts."""
        dangerous = "Entertainment<img src=x onerror=alert(1)>"
        result = sanitize_category(dangerous)
        self.assertNotIn('<img', result)
        self.assertNotIn('onerror', result)
        self.assertIn('Entertainment', result)
    
    def test_sanitize_category_preserves_hyphenated(self):
        """Test that sanitize_category preserves hyphenated categories."""
        safe = "Emergency-Fund"
        result = sanitize_category(safe)
        self.assertIn('Emergency', result)
        self.assertIn('Fund', result)
    
    def test_sanitize_category_limits_length(self):
        """Test that sanitize_category enforces max length."""
        long_cat = "C" * 150
        result = sanitize_category(long_cat)
        self.assertLessEqual(len(result), 100)
    
    # === SANITIZE CURRENCY SYMBOL TESTS ===
    
    def test_sanitize_currency_symbol_preserves_safe(self):
        """Test that sanitize_currency_symbol preserves safe symbols."""
        symbols = ["$", "€", "£", "¥", "₹"]
        for symbol in symbols:
            result = sanitize_currency_symbol(symbol)
            self.assertIsNotNone(result)
            self.assertGreater(len(result), 0)
    
    def test_sanitize_currency_symbol_removes_dangerous(self):
        """Test that sanitize_currency_symbol removes dangerous content."""
        dangerous = "$<script>alert(1)</script>"
        result = sanitize_currency_symbol(dangerous)
        self.assertNotIn('<script>', result)
    
    def test_sanitize_currency_symbol_limits_length(self):
        """Test that sanitize_currency_symbol limits to 3 chars."""
        long_symbol = "XXXXXX"
        result = sanitize_currency_symbol(long_symbol)
        self.assertLessEqual(len(result), 3)
    
    def test_sanitize_currency_symbol_handles_none(self):
        """Test that sanitize_currency_symbol defaults to $."""
        result = sanitize_currency_symbol(None)
        self.assertEqual(result, "$")
    
    # === SANITIZE AMOUNT TESTS ===
    
    def test_sanitize_amount_preserves_numbers(self):
        """Test that sanitize_amount preserves numeric values."""
        amounts = ["1500.50", "-100", "1000", "999,999.99"]
        for amount in amounts:
            result = sanitize_amount(amount)
            # Should preserve digits and separators
            self.assertTrue(any(c.isdigit() for c in result))
    
    def test_sanitize_amount_removes_dangerous_chars(self):
        """Test that sanitize_amount removes dangerous characters."""
        dangerous = "1500<script>alert(1)</script>"
        result = sanitize_amount(dangerous)
        self.assertNotIn('<script>', result)
        self.assertTrue(any(c.isdigit() for c in result))
    
    def test_sanitize_amount_handles_negative(self):
        """Test that sanitize_amount handles negative amounts."""
        negative = "-150.50"
        result = sanitize_amount(negative)
        self.assertIn('-', result)
        self.assertIn('150', result)
    
    def test_sanitize_amount_limits_length(self):
        """Test that sanitize_amount limits to 20 chars."""
        long_amount = "1" * 30
        result = sanitize_amount(long_amount)
        self.assertLessEqual(len(result), 20)
    
    # === SANITIZE DICT VALUES TESTS ===
    
    def test_sanitize_dict_values_sanitizes_strings(self):
        """Test that sanitize_dict_values sanitizes string values."""
        data = {
            'name': '<script>alert(1)</script>Test',
            'amount': 1500,
            'category': 'Entertainment<img src=x>'
        }
        result = sanitize_dict_values(data)
        self.assertNotIn('<script>', result['name'])
        self.assertEqual(result['amount'], 1500)  # Non-strings unchanged
        self.assertNotIn('<img', result['category'])
    
    def test_sanitize_dict_values_preserves_numbers(self):
        """Test that sanitize_dict_values preserves numeric types."""
        data = {
            'score': 85.5,
            'count': 10,
            'text': 'Revenue'
        }
        result = sanitize_dict_values(data)
        self.assertEqual(result['score'], 85.5)
        self.assertEqual(result['count'], 10)
    
    def test_sanitize_dict_values_handles_none(self):
        """Test that sanitize_dict_values handles None input."""
        result = sanitize_dict_values(None)
        self.assertEqual(result, {})
    
    # === IS SAFE TO DISPLAY TESTS ===
    
    def test_is_safe_to_display_detects_script_tag(self):
        """Test that is_safe_to_display detects script tags."""
        dangerous = "Hello <script>alert(1)</script>"
        result = is_safe_to_display(dangerous)
        self.assertFalse(result)
    
    def test_is_safe_to_display_detects_javascript_protocol(self):
        """Test that is_safe_to_display detects javascript: protocol."""
        dangerous = "Click here: javascript:alert(1)"
        result = is_safe_to_display(dangerous)
        self.assertFalse(result)
    
    def test_is_safe_to_display_detects_onerror(self):
        """Test that is_safe_to_display detects onerror handlers."""
        dangerous = "<img onerror='alert(1)'>"
        result = is_safe_to_display(dangerous)
        self.assertFalse(result)
    
    def test_is_safe_to_display_detects_iframe(self):
        """Test that is_safe_to_display detects iframe tags."""
        dangerous = "<iframe src='evil.com'></iframe>"
        result = is_safe_to_display(dangerous)
        self.assertFalse(result)
    
    def test_is_safe_to_display_detects_eval(self):
        """Test that is_safe_to_display detects eval() calls."""
        dangerous = "eval(document.write())"
        result = is_safe_to_display(dangerous)
        self.assertFalse(result)
    
    def test_is_safe_to_display_allows_safe_text(self):
        """Test that is_safe_to_display allows safe text."""
        safe = "This is a safe message with numbers 123 and symbols !@#"
        result = is_safe_to_display(safe)
        self.assertTrue(result)
    
    def test_is_safe_to_display_allows_special_chars(self):
        """Test that is_safe_to_display allows special characters."""
        safe = "Price: $1500 & 30% off!"
        result = is_safe_to_display(safe)
        self.assertTrue(result)
    
    def test_is_safe_to_display_case_insensitive(self):
        """Test that is_safe_to_display is case-insensitive."""
        dangerous_upper = "JAVASCRIPT:alert(1)"
        result = is_safe_to_display(dangerous_upper)
        self.assertFalse(result)
    
    def test_is_safe_to_display_handles_none(self):
        """Test that is_safe_to_display handles None input."""
        result = is_safe_to_display(None)
        self.assertTrue(result)
    
    # === INTEGRATION TESTS ===
    
    def test_xss_payload_multiple_vectors(self):
        """Test sanitization against multiple XSS vectors."""
        payloads = [
            "<svg onload=alert(1)>",
            "<body onload=alert(1)>",
            "<img src=x onerror=alert(1)>",
            "<iframe srcdoc='<script>alert(1)</script>'>",
            "<embed src='x' onerror=alert(1)>",
        ]
        
        for payload in payloads:
            result = sanitize_text(payload)
            # Should not contain dangerous keywords
            self.assertNotIn('onload', result.lower())
            self.assertNotIn('onerror', result.lower())
            self.assertNotIn('srcdoc', result.lower())
    
    def test_sql_injection_in_category(self):
        """Test that category sanitization handles SQL-like input."""
        sql_injection = "'; DROP TABLE users; --"
        result = sanitize_category(sql_injection)
        # Should preserve the text but it's safe
        self.assertIsNotNone(result)
    
    def test_real_world_category_names(self):
        """Test sanitization with real-world category names."""
        categories = [
            "Groceries",
            "Entertainment & Events",
            "Gas/Fuel",
            "Rent/Mortgage",
            "Electric-Utilities",
            "Phone & Internet",
            "Car-Insurance",
            "Eating Out",
            "Gym & Fitness",
            "Books & Media",
        ]
        
        for category in categories:
            result = sanitize_category(category)
            # Should preserve the category meaning
            self.assertGreater(len(result), 0)
            # Check at least 1 word is preserved
            words = category.split()
            self.assertTrue(any(word in result for word in words))


if __name__ == '__main__':
    unittest.main()
