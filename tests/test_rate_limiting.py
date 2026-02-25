"""Tests for rate limiting and throttling functionality."""

import time
import unittest
from src.finance_app.rate_limiting import (
    RateLimiter, rate_limit, exponential_backoff,
    validate_file_size, get_rate_limiter_status,
    API_CALLS_PER_MINUTE, API_CALL_TIMEOUT_SECONDS
)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality."""

    def test_rate_limiter_allows_calls_within_limit(self):
        """Test that calls within limit are allowed."""
        limiter = RateLimiter(max_calls=3, time_window=10)
        
        self.assertTrue(limiter.is_allowed())
        self.assertTrue(limiter.is_allowed())
        self.assertTrue(limiter.is_allowed())
        self.assertFalse(limiter.is_allowed())  # 4th call denied

    def test_rate_limiter_reset_after_window(self):
        """Test that rate limiter resets after time window."""
        limiter = RateLimiter(max_calls=1, time_window=1)
        
        self.assertTrue(limiter.is_allowed())
        self.assertFalse(limiter.is_allowed())
        
        time.sleep(1.1)
        self.assertTrue(limiter.is_allowed())  # Should be allowed after window

    def test_validate_file_size_within_limit(self):
        """Test file size validation within limit."""
        result = validate_file_size(file_size_mb=10.0, max_size_mb=50.0)
        self.assertTrue(result)

    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation when exceeding limit."""
        result = validate_file_size(file_size_mb=60.0, max_size_mb=50.0)
        self.assertFalse(result)

    def test_validate_file_size_none(self):
        """Test file size validation with None."""
        result = validate_file_size(file_size_mb=None, max_size_mb=50.0)
        self.assertTrue(result)


class TestExponentialBackoff(unittest.TestCase):
    """Test exponential backoff functionality."""

    def test_exponential_backoff_succeeds_first_try(self):
        """Test backoff when function succeeds on first try."""
        @exponential_backoff(max_retries=3, initial_backoff=0.01)
        def successful_func():
            return "success"
        
        result = successful_func()
        self.assertEqual(result, "success")

    def test_exponential_backoff_retries_then_succeeds(self):
        """Test backoff retries and eventually succeeds."""
        call_count = {'count': 0}
        
        @exponential_backoff(max_retries=3, initial_backoff=0.01)
        def eventually_succeeds():
            call_count['count'] += 1
            if call_count['count'] < 2:
                raise ValueError("Temp error")
            return "success"
        
        result = eventually_succeeds()
        self.assertEqual(result, "success")
        self.assertEqual(call_count['count'], 2)

    def test_exponential_backoff_max_retries_exceeded(self):
        """Test backoff fails after max retries."""
        @exponential_backoff(max_retries=2, initial_backoff=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            always_fails()


class TestRateLimiterStatus(unittest.TestCase):
    """Test rate limiter status reporting."""

    def test_get_rate_limiter_status(self):
        """Test getting rate limiter status."""
        status = get_rate_limiter_status()
        
        self.assertIn('current_calls', status)
        self.assertIn('max_calls', status)
        self.assertIn('time_window', status)
        self.assertIn('calls_remaining', status)
        self.assertIn('rate_limited', status)
        
        self.assertEqual(status['max_calls'], API_CALLS_PER_MINUTE)
        self.assertEqual(status['time_window'], API_CALL_TIMEOUT_SECONDS)


if __name__ == '__main__':
    unittest.main()
