import os
from datetime import datetime

# === FILE PATHS ===
# Path to currencies data file (supports multiple currencies)
CURRENCIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'currencies.json')

# Log file for application events
LOG_FILE = 'app.log'

# Template file name for Excel export (example data for users)
TEMPLATE_FILE = 'Finance Check 50_30_20 Templates.xlsx'

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

# === CHART VISUALIZATION SETTINGS ===
# Standard chart dimensions for PDF embedding
CHART_WIDTH = 400
CHART_HEIGHT = 500