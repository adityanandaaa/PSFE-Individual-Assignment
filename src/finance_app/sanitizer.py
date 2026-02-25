"""Input sanitization module for XSS/injection prevention.

This module provides sanitization functions to prevent XSS (Cross-Site Scripting)
and injection attacks by cleaning user inputs and data before display.

Sanitization is particularly important when:
- Displaying file names from user uploads
- Showing category names in charts and PDFs
- Rendering user-provided text in reports
- Embedding data in HTML/PDF contexts
"""

import bleach
import html
from typing import Optional


def sanitize_text(text: str, max_length: int = 150) -> str:
    """Sanitize general text input to prevent XSS/injection attacks.
    
    Removes HTML tags, JavaScript, and other dangerous content while
    preserving the text for safe display. Applied to:
    - Category names
    - File names
    - User-provided text fields
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default 150 chars)
        
    Returns:
        str: Sanitized text safe for display
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Use bleach to strip all HTML tags and dangerous content
    # tags=[] means no tags are allowed
    # strip=True removes disallowed tags instead of escaping them
    sanitized = bleach.clean(
        text,
        tags=[],           # No HTML tags allowed
        strip=True,        # Strip tags instead of escaping
        attributes={},     # No attributes allowed
    )
    
    # HTML-escape any remaining special characters
    sanitized = html.escape(sanitized)
    
    return sanitized.strip()


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize file names to prevent path traversal and injection attacks.
    
    Removes dangerous characters and path elements while preserving
    the meaningful filename. Applied to:
    - Uploaded Excel file names
    - Generated PDF file names
    - Template file names
    
    Args:
        filename: Input file name to sanitize
        max_length: Maximum allowed length (default 255 chars)
        
    Returns:
        str: Sanitized filename safe for filesystem operations
    """
    if not filename or not isinstance(filename, str):
        return "file"
    
    # Remove path separators to prevent path traversal
    filename = filename.replace("/", "").replace("\\", "").replace(".", "")
    
    # Use bleach to strip all tags
    sanitized = bleach.clean(
        filename,
        tags=[],
        strip=True,
        attributes={},
    )
    
    # HTML-escape special characters
    sanitized = html.escape(sanitized)
    
    # Truncate to max length
    sanitized = sanitized[:max_length]
    
    return sanitized.strip() or "file"


def sanitize_category(category: str) -> str:
    """Sanitize category names for safe display in charts/reports.
    
    Category names come from user Excel files and should be cleaned
    before display in PDFs or charts to prevent injection attacks.
    
    Args:
        category: Category name from data
        
    Returns:
        str: Sanitized category name
    """
    # Categories should be single-word or hyphenated (already validated)
    # Still sanitize for extra safety
    return sanitize_text(category, max_length=100)


def sanitize_currency_symbol(symbol: str) -> str:
    """Sanitize currency symbols to prevent injection.
    
    Currency symbols should be simple characters but we sanitize
    to be safe in case of data corruption or malicious input.
    
    Args:
        symbol: Currency symbol (e.g., "$", "€")
        
    Returns:
        str: Sanitized currency symbol
    """
    # Currency symbols are typically 1-3 characters
    if not symbol or not isinstance(symbol, str):
        return "$"
    
    # Bleach clean and limit to 3 characters
    sanitized = bleach.clean(symbol, tags=[], strip=True, attributes={})
    sanitized = html.escape(sanitized)
    
    return sanitized[:3] if sanitized else "$"


def sanitize_amount(amount_str: str) -> str:
    """Sanitize numeric amount strings to prevent injection.
    
    Amount values are typically numeric but we sanitize for safe
    display in reports and logs.
    
    Args:
        amount_str: Amount as string (e.g., "1500.50")
        
    Returns:
        str: Sanitized amount string
    """
    if not amount_str or not isinstance(amount_str, str):
        return "0.00"
    
    # Only allow digits, comma, and decimal point
    sanitized = "".join(c for c in amount_str if c.isdigit() or c in ',.+-')
    
    return sanitized[:20] if sanitized else "0.00"  # Max 20 chars (e.g., "-999,999,999.99")


def sanitize_dict_values(data: dict) -> dict:
    """Sanitize all string values in a dictionary.
    
    Useful for sanitizing entire result dictionaries before
    display or logging.
    
    Args:
        data: Dictionary with mixed value types
        
    Returns:
        dict: Dictionary with sanitized string values
    """
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        else:
            sanitized[key] = value
    
    return sanitized


def is_safe_to_display(text: str) -> bool:
    """Check if text is safe to display without sanitization.
    
    Useful for validation before rendering. Returns True if
    text contains no dangerous patterns.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text appears safe
    """
    if not text or not isinstance(text, str):
        return True
    
    # Check for common XSS patterns
    dangerous_patterns = [
        '<script',
        'javascript:',
        'onerror=',
        'onload=',
        '<iframe',
        '<object',
        '<embed',
        'onclick=',
        'eval(',
    ]
    
    text_lower = text.lower()
    return not any(pattern in text_lower for pattern in dangerous_patterns)
