"""
LOGGING CONFIGURATION MODULE
=============================

This module provides centralized logging configuration for the Finance Health Check application.
It controls log output to both file and console with configurable levels and formats.

Usage:
    from finance_app.logging_config import setup_logging
    logger = setup_logging(log_level=logging.INFO, log_file='app.log')
    logger.info("Application started")
"""

import logging
import os
from pathlib import Path


class LogLevelConfig:
    """Constants for logging levels and their descriptions."""
    DEBUG = logging.DEBUG        # 10 - Detailed debug information
    INFO = logging.INFO          # 20 - General information (default)
    WARNING = logging.WARNING    # 30 - Warning messages
    ERROR = logging.ERROR        # 40 - Error messages
    CRITICAL = logging.CRITICAL  # 50 - Critical errors
    
    LEVEL_NAMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARNING: "WARNING",
        ERROR: "ERROR",
        CRITICAL: "CRITICAL"
    }


def setup_logging(log_level=logging.INFO, log_file='app.log', 
                  console_level=logging.WARNING, max_bytes=10*1024*1024,
                  backup_count=5):
    """
    Configure logging for the application with file and console handlers.
    
    This function sets up:
    - File handler: Logs all messages to file (rotating based on size)
    - Console handler: Logs only warnings+ to terminal
    - Formatter: Consistent timestamp, level, and message format
    
    Args:
        log_level (int): File logging level (DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
        log_file (str): Path to log file (relative or absolute)
        console_level (int): Console logging level (WARNING=30 by default)
        max_bytes (int): Maximum size of log file before rotation (default: 10MB)
        backup_count (int): Number of backup log files to keep (default: 5)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Examples:
        >>> # Basic setup with INFO level
        >>> logger = setup_logging(log_level=logging.INFO, log_file='app.log')
        >>> logger.info("Application started")
        
        >>> # Debug level with larger log files
        >>> logger = setup_logging(log_level=logging.DEBUG, max_bytes=50*1024*1024)
        
        >>> # Minimal logging (only errors)
        >>> logger = setup_logging(log_level=logging.ERROR)
    """
    # Create logger instance
    logger = logging.getLogger()
    
    # Only configure if not already configured (prevents duplicate handlers)
    if logger.handlers:
        return logger
    
    # Set overall logger level (lowest level it will accept)
    logger.setLevel(min(log_level, console_level))
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ====== FILE HANDLER ======
    # Logs all messages to app.log (with rotation)
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
    except Exception:
        # Fallback to basic FileHandler if RotatingFileHandler fails
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
    
    # ====== CONSOLE HANDLER ======
    # Logs warnings+ to terminal/console (minimal noise)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    
    # ====== FORMATTER ======
    # Consistent format: timestamp - level - message
    # Example: 2026-01-27 14:30:45 - INFO - File validated successfully
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance (assumes setup_logging was called first).
    
    Args:
        name (str, optional): Logger name (usually __name__)
    
    Returns:
        logging.Logger: Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    return logging.getLogger(name)


def set_log_level(level):
    """
    Dynamically change logging level at runtime.
    
    Args:
        level (int): New logging level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)
    
    Example:
        >>> set_log_level(logging.DEBUG)  # Enable debug logging
        >>> set_log_level(logging.ERROR)  # Only errors
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.setLevel(level)


def get_log_level_name(level):
    """
    Get human-readable name for a logging level.
    
    Args:
        level (int): Logging level number
    
    Returns:
        str: Level name (e.g., "INFO", "DEBUG")
    
    Example:
        >>> get_log_level_name(logging.INFO)
        'INFO'
    """
    return LogLevelConfig.LEVEL_NAMES.get(level, "UNKNOWN")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
"""
# In your main application file:

from finance_app.logging_config import setup_logging, get_logger
import logging

# Initialize logging (call once at app startup)
logger = setup_logging(
    log_level=logging.INFO,        # Log INFO+ to file
    log_file='app.log',             # Log file path
    console_level=logging.WARNING   # Only WARNING+ to console
)

# Use logger throughout the app
logger.debug("Debug message (file only)")
logger.info("Info message (file only)")
logger.warning("Warning message (file and console)")
logger.error("Error message (file and console)")
logger.critical("Critical message (file and console)")

# Change log level dynamically
set_log_level(logging.DEBUG)  # Enable debug
logger.debug("Now visible")

# Get logger in other modules
from finance_app.logging_config import get_logger
module_logger = get_logger(__name__)
module_logger.info("Message from module")
"""
