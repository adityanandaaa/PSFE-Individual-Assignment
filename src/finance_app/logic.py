import pandas as pd
import json
import logging
from datetime import datetime
from functools import lru_cache
from finance_app.config import CURRENCIES_FILE
from finance_app.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)

@lru_cache(maxsize=1)
def load_currencies():
    """Load currencies from JSON file (cached)."""
    try:
        # Attempt to open and parse the currencies JSON file
        with open(CURRENCIES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Log error if file does not exist and return empty list as fallback
        logger.error("currencies.json not found.")
        return []

def is_valid_income(income):
    """Validate income input - must be numeric and positive."""
    try:
        # Convert input to float (handles both numeric and string inputs)
        val = float(income)
        # Check if income is greater than zero (negative or zero income is invalid)
        return val > 0
    except (ValueError, TypeError):
        # Return False if conversion fails (non-numeric input)
        return False

def get_currency_symbol(currencies, code):
    """Get currency symbol by code from the currencies list."""
    # Find currency object with matching code (case-sensitive)
    currency = next((c for c in currencies if c['code'] == code), None)
    # Return symbol if found, otherwise None
    return currency['symbol'] if currency else None

def validate_file(file_path):
    """Validate the uploaded Excel file structure and content.
    
    Returns:
        tuple: (is_valid: bool, result: pd.DataFrame or list of (row_num, error_msg) tuples)
    """
    try:
        # Load Excel file using openpyxl engine for better compatibility
        # Use context manager to ensure file is properly closed after reading
        from openpyxl import load_workbook
        wb = load_workbook(file_path)
        ws = wb.active
        
        # Read data into DataFrame from worksheet
        data = []
        headers = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = row
            else:
                data.append(row)
        
        df = pd.DataFrame(data, columns=headers)

        # Normalize: keep only required columns, drop fully empty rows
        required_cols = ['Date', 'Name', 'Type', 'Amount', 'Category']
        # Remove rows where all required fields are empty/NaN/whitespace
        df = (
            df[required_cols]
            .replace(r'^\s*$', pd.NA, regex=True)
            .dropna(how='all')
            .reset_index(drop=True)
        )
        wb.close()  # Explicitly close the workbook to release file lock
        
        errors = []  # List of (row_num, error_msg) tuples
        
        # Check if all required columns exist
        if not all(col in df.columns for col in required_cols):
            errors.append((0, "Missing required columns."))
        
        # Iterate through each row to validate data
        for idx, row in df.iterrows():
            # === DATE VALIDATION ===
            if pd.isna(row['Date']):
                errors.append((idx+1, "Date is empty."))
            else:
                # Accept Excel datetime serials or datetime/Timestamp objects as-is
                date_val = row['Date']
                try:
                    if isinstance(date_val, (datetime, pd.Timestamp)):
                        parsed_date = pd.to_datetime(date_val, errors='coerce')
                    elif isinstance(date_val, (int, float)):
                        # Excel serial dates are numeric; let pandas convert
                        parsed_date = pd.to_datetime(date_val, errors='coerce', unit='D', origin='1899-12-30')
                    else:
                        # For strings, enforce dd/mm/YYYY (with slash or dash)
                        parsed_date = pd.to_datetime(date_val, errors='coerce', format='%d/%m/%Y')
                        if pd.isna(parsed_date):
                            parsed_date = pd.to_datetime(date_val, errors='coerce', format='%d-%m-%Y')
                    if pd.isna(parsed_date):
                        errors.append((idx+1, "Invalid date format."))
                except Exception:
                    errors.append((idx+1, "Invalid date format."))
            
            # === NAME VALIDATION ===
            # Check: not empty, is string, max 150 chars, contains alphanumeric + spaces
            if pd.isna(row['Name']) or not isinstance(row['Name'], str) or len(str(row['Name'])) > 150 or str(row['Name']).replace(' ', '').isalnum() == False:
                errors.append((idx+1, "Invalid name."))
            
            # === TYPE VALIDATION ===
            # Type must be one of the three budget categories
            if row['Type'] not in ['Needs', 'Wants', 'Savings']:
                errors.append((idx+1, "Invalid type."))
            
            # === AMOUNT VALIDATION ===
            try:
                # Convert amount to float for numeric validation (allow commas)
                amt_str = str(row['Amount']).replace(',', '')
                amt = float(amt_str)
                # Amount must be positive
                if amt <= 0:
                    errors.append((idx+1, "Invalid amount."))
                else:
                    # Check decimal places - maximum 3 decimal places allowed (e.g., 10.999)
                    s = str(row['Amount'])
                    if '.' in s:
                        dec = s.split('.')[-1]
                        if len(dec) > 3:
                            errors.append((idx+1, "Invalid amount."))
            except Exception:
                # Amount conversion failed
                errors.append((idx+1, "Invalid amount."))
            
            # === CATEGORY VALIDATION ===
            # Check: not empty, is string, max 150 chars
            if pd.isna(row['Category']) or not isinstance(row['Category'], str) or len(str(row['Category'])) > 150:
                errors.append((idx+1, "Invalid category."))
        
        # Return results based on whether any errors were found
        if errors:
            return False, errors
        return True, df
    except Exception as e:
        # Handle any file reading errors
        return False, [(0, f"Error reading file: {str(e)}")]

def analyze_data(df, income):
    """Analyze financial data and calculate budget allocation.
    
    Aggregates spending by Type (Needs, Wants, Savings) and calculates
    the top 5 spending categories within Wants for detailed analysis.
    
    Args:
        df: DataFrame with columns [Date, Name, Type, Amount, Category]
        income: Total monthly income for reference
        
    Returns:
        tuple: (needs, wants, savings, top_wants_series)
    """
    # Normalize category names to lowercase for consistent grouping
    df['Category'] = df['Category'].str.lower()
    
    # Group by Type and sum amounts for each budget category
    buckets = df.groupby('Type')['Amount'].sum()
    
    # Extract total amounts for each budget category (use .get() for safety if missing)
    needs = buckets.get('Needs', 0)
    wants = buckets.get('Wants', 0)
    savings = buckets.get('Savings', 0)
    
    # === TOP WANTS ANALYSIS ===
    # Filter for only 'Wants' type transactions
    wants_df = df[df['Type'] == 'Wants']
    # Group wants by category and get top 5 by total amount
    top_wants = wants_df.groupby('Category')['Amount'].sum().nlargest(5)
    
    # Return aggregated budget data
    return needs, wants, savings, top_wants

def calculate_health_score(income, needs, wants, savings):
    """Calculate monthly budget health score based on 50/30/20 budgeting model.
    
    Uses directional deviation logic to penalize only risky behaviors:
    - Needs overspend (> 50%) - small penalty
    - Wants overspend (> 30%) - heavier penalty
    - Under-saving (< 20%) - heaviest penalty
    
    Weighted deviations:
    Dn = max(0, n - 0.5)      # Needs overspend
    Dw = max(0, w - 0.3)      # Wants overspend
    Ds = max(0, 0.2 - s)      # Under-saving
    Score = 100 × (1 - (0.2×Dn + 0.5×Dw + 0.6×Ds))
    
    Hard risk rules:
    - If savings < 0: Score = 0 (financial danger - debt/overspend)
    - If needs > 75%: Score -= 10 (extreme overspend)
    
    Final score is clamped to [0, 100].
    
    Args:
        income: Total monthly income
        needs: Total needs spending
        wants: Total wants spending
        savings: Total savings
        
    Returns:
        int: Health score from 0 to 100
    """
    # === STEP 1: CALCULATE RATIOS ===
    # Prevent division by zero
    if income <= 0:
        return 0
    
    # Convert spending to ratios (as fractions of income)
    n = needs / income      # Needs ratio
    w = wants / income      # Wants ratio
    s = savings / income    # Savings ratio
    
    # === STEP 2: DIRECTIONAL DEVIATIONS (only penalize risk) ===
    # Only measure overspend/under-save, not underspend/over-save
    Dn = max(0, n - 0.5)      # Needs overspend (penalty only if > 50%)
    Dw = max(0, w - 0.3)      # Wants overspend (penalty only if > 30%)
    Ds = max(0, 0.2 - s)      # Under-saving (penalty only if < 20%)
    
    # === STEP 3: WEIGHTED SCORE CALCULATION ===
    # Weights: Needs 0.2, Wants 0.5, Savings 0.6
    # Higher weights on Wants and Savings reflect their importance to financial health
    score = 100 * (1 - (0.2 * Dn + 0.5 * Dw + 0.6 * Ds))
    
    # === STEP 4: HARD MONTHLY RISK RULES ===
    # Severe penalty: negative savings means debt or overspending
    if savings < 0:
        score = 0
    
    # Penalize extreme needs overspend (> 75%)
    if n > 0.75:
        score -= 10
    
    # === STEP 5: CLAMP TO 0–100 ===
    score = max(0, min(100, score))
    
    return int(score)