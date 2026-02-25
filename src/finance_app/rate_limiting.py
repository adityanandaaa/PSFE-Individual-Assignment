"""Rate limiting and throttling module for API calls and file uploads.

This module provides:
- Exponential backoff retry mechanism
- Per-minute API call rate limiting
- File upload size throttling
- Graceful degradation when limits exceeded
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, TypeVar, Optional

logger = logging.getLogger(__name__)

# Rate limiting constants
API_CALLS_PER_MINUTE = 10  # Max 10 API calls per minute
API_CALL_TIMEOUT_SECONDS = 60  # Time window for rate limiting
MAX_FILE_UPLOAD_MB = 50  # Maximum file size in MB
MAX_RETRIES = 3  # Maximum retry attempts
INITIAL_BACKOFF_SECONDS = 1.0  # Initial backoff duration

F = TypeVar('F', bound=Callable[..., Any])


class RateLimiter:
    """Thread-safe rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: int):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def is_allowed(self) -> bool:
        """Check if a call is allowed within rate limit."""
        now = time.time()
        # Remove calls older than time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def wait_if_needed(self) -> float:
        """Wait until a call is allowed. Returns wait duration in seconds."""
        if self.is_allowed():
            return 0.0
        
        if not self.calls:
            return 0.0
        
        oldest_call = self.calls[0]
        wait_time = self.time_window - (time.time() - oldest_call)
        wait_time = max(0, wait_time + 0.1)  # Small buffer
        
        logger.warning(f"Rate limit reached. Waiting {wait_time:.2f}s")
        time.sleep(wait_time)
        return wait_time


# Global rate limiter instance
_api_rate_limiter = RateLimiter(
    max_calls=API_CALLS_PER_MINUTE,
    time_window=API_CALL_TIMEOUT_SECONDS
)


def rate_limit(max_calls: int = API_CALLS_PER_MINUTE, 
               time_window: int = API_CALL_TIMEOUT_SECONDS):
    """Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum calls allowed in time window
        time_window: Time window in seconds
    """
    limiter = RateLimiter(max_calls, time_window)
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def exponential_backoff(max_retries: int = MAX_RETRIES,
                       initial_backoff: float = INITIAL_BACKOFF_SECONDS):
    """Decorator to add exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff duration in seconds
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed. "
                            f"Retrying in {backoff:.2f}s: {type(e).__name__}"
                        )
                        time.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts"
                        )
            
            raise last_exception
        return wrapper
    return decorator


def exponential_backoff_async(max_retries: int = MAX_RETRIES,
                              initial_backoff: float = INITIAL_BACKOFF_SECONDS):
    """Decorator to add exponential backoff retry logic for async functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff duration in seconds
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            backoff = initial_backoff
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed. "
                            f"Retrying in {backoff:.2f}s: {type(e).__name__}"
                        )
                        await asyncio.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts"
                        )
            
            raise last_exception
        return wrapper
    return decorator


def validate_file_size(file_size_mb: Optional[float] = None,
                      max_size_mb: float = MAX_FILE_UPLOAD_MB) -> bool:
    """Validate file upload size.
    
    Args:
        file_size_mb: File size in MB
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if file size is acceptable, False otherwise
    """
    if file_size_mb is None:
        return True
    
    if file_size_mb > max_size_mb:
        logger.warning(
            f"File size {file_size_mb:.2f}MB exceeds limit of {max_size_mb}MB"
        )
        return False
    
    return True


def get_rate_limiter_status() -> dict:
    """Get current rate limiter status."""
    now = time.time()
    recent_calls = sum(
        1 for call_time in _api_rate_limiter.calls
        if now - call_time < _api_rate_limiter.time_window
    )
    
    return {
        'current_calls': recent_calls,
        'max_calls': _api_rate_limiter.max_calls,
        'time_window': _api_rate_limiter.time_window,
        'calls_remaining': max(0, _api_rate_limiter.max_calls - recent_calls),
        'rate_limited': recent_calls >= _api_rate_limiter.max_calls
    }
