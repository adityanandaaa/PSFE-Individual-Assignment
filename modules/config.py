import os

# Configuration constants
CURRENCIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'currencies.json')
LOG_FILE = 'app.log'
TEMPLATE_FILE = 'Finance Check 50_30_20 Templates.xlsx'
PDF_FILE = 'financial_report.pdf'
DOWNLOADS_PATH = os.path.expanduser('~/Downloads')

# Chart settings
CHART_WIDTH = 400
CHART_HEIGHT = 500