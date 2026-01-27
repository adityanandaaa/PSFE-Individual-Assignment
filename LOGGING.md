# Logging Configuration Guide

## Overview

The Finance Health Check application uses a comprehensive logging system to track application events, errors, and debug information. The logging configuration provides:

- **Detailed file logging**: All INFO+ messages saved to `app.log`
- **Minimal console output**: Only WARNING+ messages to terminal (reduces noise)
- **Automatic log rotation**: Log files rotate at 10MB to prevent disk space issues
- **Backup logs**: Up to 5 backup log files maintained automatically

## Configuration Details

### File Handler
- **Output**: `app.log` (in project root)
- **Level**: INFO (logs INFO, WARNING, ERROR, CRITICAL)
- **Size Limit**: 10MB per file
- **Rotation**: Automatic when file exceeds 10MB
- **Backup Count**: 5 backup files (app.log.1, app.log.2, etc.)

### Console Handler
- **Output**: Terminal/stdout
- **Level**: WARNING (logs WARNING, ERROR, CRITICAL only)
- **Purpose**: Minimize terminal noise while alerting to important issues

### Log Format
```
YYYY-MM-DD HH:MM:SS - LEVEL - Message
Example: 2026-01-27 14:30:45 - INFO - File validated successfully
```

## Logging Levels

| Level | Value | Description | Usage |
|-------|-------|-------------|-------|
| DEBUG | 10 | Detailed debug information | Development/troubleshooting only |
| INFO | 20 | General informational messages | Normal operation events (default) |
| WARNING | 30 | Warning messages | Potential issues (shown in console) |
| ERROR | 40 | Error messages | Failed operations (shown in console) |
| CRITICAL | 50 | Critical errors | System failures (shown in console) |

## Usage Examples

### Basic Setup (Application Start)
```python
from finance_app.logging_config import setup_logging
import logging

# Initialize logging (call once at app startup)
logger = setup_logging(
    log_level=logging.INFO,        # INFO+ to file
    log_file='app.log',             # Log file location
    console_level=logging.WARNING,  # WARNING+ to console
    max_bytes=10*1024*1024,         # 10MB per file
    backup_count=5                  # Keep 5 backups
)
```

### Using Logger in Modules
```python
from finance_app.logging_config import get_logger
import logging

# Get module logger
logger = get_logger(__name__)

# Log at different levels
logger.debug("Debug info - file only")           # Not shown in console
logger.info("Normal operation - file only")      # Not shown in console
logger.warning("Warning - file AND console")     # Shows in both
logger.error("Error occurred - file AND console") # Shows in both
logger.critical("Critical issue - file AND console") # Shows in both
```

### Dynamic Log Level Changes
```python
from finance_app.logging_config import set_log_level
import logging

# Enable debug logging at runtime
set_log_level(logging.DEBUG)

# Later, reduce verbosity
set_log_level(logging.WARNING)
```

## Log File Locations

### Primary Log File
- **Location**: `/Users/macbookairm3/Finance_Health_Check/app.log`
- **Contains**: All INFO+ messages from application

### Rotated Backup Files
When `app.log` exceeds 10MB, it's renamed and a new log file is created:
- `app.log.1` - Most recent rotation
- `app.log.2` - Previous rotation
- `app.log.3`, `app.log.4`, `app.log.5` - Older backups
- Files older than 5 backups are deleted

## Example Log Output

### Console (Terminal)
```
2026-01-27 14:30:45 - WARNING - API quota exceeded, retrying in 30s
2026-01-27 14:30:46 - ERROR - Failed to generate PDF: [error details]
```

### File (app.log)
```
2026-01-27 14:30:41 - INFO - File uploaded: data.xlsx
2026-01-27 14:30:42 - INFO - File validated successfully
2026-01-27 14:30:43 - INFO - Financial analysis complete
2026-01-27 14:30:45 - WARNING - API quota exceeded, retrying in 30s
2026-01-27 14:30:46 - ERROR - Failed to generate PDF: [error details]
2026-01-27 14:30:47 - INFO - Using fallback advice template
2026-01-27 14:30:48 - INFO - PDF generated: /downloads/report.pdf
```

## Real-World Scenarios

### Debugging an Issue
1. User reports problem at 3pm
2. Check `app.log` for all activity at that time
3. Look for ERROR messages and preceding INFO messages
4. Example flow:
   ```
   14:59:30 - INFO - File uploaded: my_data.xlsx
   14:59:31 - INFO - Validating file structure
   14:59:32 - ERROR - Column 'Amount' contains non-numeric value
   14:59:33 - ERROR - File validation failed
   14:59:34 - INFO - User notified of validation error
   ```

### Monitoring API Usage
1. Check for 429 errors (quota exceeded)
2. Count ERROR messages related to API calls
3. Review retry delays from error messages
4. Plan API quota upgrade if needed

### Performance Analysis
1. Calculate time between INFO messages
2. Identify slow operations (>5 seconds)
3. Find bottlenecks in file processing
4. Optimize accordingly

## Configuration Best Practices

### Development Environment
```python
logger = setup_logging(
    log_level=logging.DEBUG,       # Detailed info
    console_level=logging.WARNING,  # Still minimal console
)
```

### Production Environment
```python
logger = setup_logging(
    log_level=logging.INFO,         # Standard info
    console_level=logging.ERROR,    # Only errors in console
    max_bytes=50*1024*1024,         # Larger files
    backup_count=10                 # More backups
)
```

### High-Security Environment
```python
logger = setup_logging(
    log_level=logging.WARNING,      # Less data logging
    console_level=logging.CRITICAL, # Only critical in console
    max_bytes=5*1024*1024,          # Smaller files
    backup_count=3                  # Fewer backups
)
```

## Troubleshooting

### Log File Not Created
- Check write permissions in project directory
- Verify `app.log` is not open in another program
- Ensure disk space available

### Missing Log Entries
- Verify logger level is set correctly (DEBUG=10, INFO=20, etc.)
- Check if handlers were properly initialized
- Ensure `setup_logging()` called before logging

### Console Too Verbose
- Increase `console_level` to `logging.ERROR`
- Remember: File still gets all INFO+ messages

### Log Files Growing Too Large
- Reduce `max_bytes` parameter (e.g., 5MB instead of 10MB)
- Increase `backup_count` to keep more history
- Manually clean old backups if needed

## API Reference

### `setup_logging(log_level, log_file, console_level, max_bytes, backup_count)`
Initialize logging with specified configuration.

**Parameters:**
- `log_level` (int): File handler level (default: INFO)
- `log_file` (str): Log file path (default: 'app.log')
- `console_level` (int): Console handler level (default: WARNING)
- `max_bytes` (int): Max log file size (default: 10MB)
- `backup_count` (int): Backup files to keep (default: 5)

**Returns:** Configured logger instance

### `get_logger(name)`
Get a logger instance for a module.

**Parameters:**
- `name` (str): Logger name (usually `__name__`)

**Returns:** Logger instance

### `set_log_level(level)`
Change logging level dynamically at runtime.

**Parameters:**
- `level` (int): New logging level (10-50)

### `get_log_level_name(level)`
Get human-readable name for a logging level.

**Parameters:**
- `level` (int): Logging level number

**Returns:** Level name string (e.g., "INFO")

## Related Files

- **Main Configuration**: `src/finance_app/logging_config.py`
- **Web App Integration**: `web_app.py` (lines ~25-40)
- **AI Module**: `src/finance_app/ai.py` (uses module logger)
- **Logic Module**: `src/finance_app/logic.py` (uses module logger)
- **Log Output**: `app.log` (created at runtime)

## Support

For issues with logging:
1. Check this guide's troubleshooting section
2. Review example log output format
3. Verify configuration in `logging_config.py`
4. Check log file permissions and disk space
