"""Log masking utility for PII protection.

This module provides a filter for the logging system that automatically
masks sensitive patterns like currency amounts, potential account names,
and other PII to ensure they don't persist in log files.
"""

import logging
import re


class SensitiveDataFilter(logging.Filter):
    """Logging filter that masks sensitive patterns in log messages."""

    def __init__(self):
        super().__init__()
        # Patterns to mask:
        # 1. Currency amounts: $1,500.00, £500, etc.
        # 2. Potential API keys (extra check)
        # 3. Large sequences of digits (potential account/card numbers)
        self.patterns = [
            # Currency amounts (symbol followed by numbers)
            (re.compile(r'([$£€¥₹]\s?|\b[A-Z]{3}\s?)(\d{1,3}(,\d{3})*(\.\d+)?)'), r'\1***'),
            # API Key looking strings (broadened pattern)
            (re.compile(r'(AIzaSy[A-Za-z0-9_-]{15,})'), 'AIzaSy***'),
            # Generic large numbers (10+ digits)
            (re.compile(r'\b\d{10,}\b'), '***'),
        ]

    def filter(self, record):
        """Mask sensitive data in the log record message."""
        if not isinstance(record.msg, str):
            return True

        original_msg = record.msg
        for pattern, replacement in self.patterns:
            original_msg = pattern.sub(replacement, original_msg)
        
        record.msg = original_msg
        
        # Also clean arguments if they are strings
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.patterns:
                        arg = pattern.sub(replacement, arg)
                new_args.append(arg)
            record.args = tuple(new_args)
            
        return True


def apply_masking(logger_instance):
    """Apply the sensitive data filter to a logger instance."""
    mask_filter = SensitiveDataFilter()
    logger_instance.addFilter(mask_filter)
    return logger_instance
