import os
from datetime import datetime
import logging
from finance_app.models import EnvConfig
from pydantic import ValidationError

# Get logger
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate project environment variables against schema.
    
    This provides 'Environment Protection' by ensuring required keys 
    like GEMINI_API_KEY meet minimum length and format requirements.
    """
    try:
        # Load and validate environment configuration
        config = EnvConfig(
            gemini_api_key=os.getenv('GEMINI_API_KEY', '')
        )
        return config
    except ValidationError as e:
        logger.critical(f"Environment configuration failed validation: {str(e)}")
        # If in a production context, you might want to raise an error
        # return None for now so the app can handle it gracefully
        return None

# === FILE PATHS ===
# Path to currencies data file (supports multiple currencies)
# Point to project-level data/currencies.json (src/finance_app → project root → data)
CURRENCIES_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'currencies.json')

# Log file for application events
LOG_FILE = 'app.log'

# Template file name for Excel export (example data for users)
TEMPLATE_FILE = 'Finance Health Check 50_30_20 Templates.xlsx'

# Output PDF report file name prefix (timestamp will be added for uniqueness)
PDF_FILE = 'financial_report.pdf'

# User's Downloads folder (where templates and reports are saved)
DOWNLOADS_PATH = os.path.expanduser('~/Downloads')

def get_pdf_filename():
    """Generate unique PDF filename with timestamp to avoid collisions.
    
    Creates filenames like: financial_report_20260126_143022.pdf
    This prevents overwriting existing reports when generating multiple times.
    
    Returns:
        str: Unique PDF filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'financial_report_{timestamp}.pdf'

def get_template_filename():
    """Generate unique template filename with timestamp to avoid collisions.
    
    Creates filenames like: Finance Health Check 50_30_20 Templates_20260126_143022.xlsx
    This allows users to download multiple template copies without overwriting.
    
    Returns:
        str: Unique template filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'Finance Health Check 50_30_20 Templates_{timestamp}.xlsx'

# === CHART VISUALIZATION SETTINGS ===
# Standard chart dimensions for PDF embedding
CHART_WIDTH = 400
CHART_HEIGHT = 500