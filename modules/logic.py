import pandas as pd
import json
import logging
from datetime import datetime
from modules.config import CURRENCIES_FILE

def load_currencies():
    """Load currencies from JSON file."""
    try:
        with open(CURRENCIES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("currencies.json not found.")
        return []

def is_valid_income(income):
    """Validate income input."""
    try:
        val = float(income)
        return val > 0
    except (ValueError, TypeError):
        return False

def get_currency_symbol(currencies, code):
    """Get currency symbol by code."""
    currency = next((c for c in currencies if c['code'] == code), None)
    return currency['symbol'] if currency else None

def validate_file(file_path):
    """Validate the uploaded Excel file."""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        errors = []
        required_cols = ['Date', 'Name', 'Type', 'Amount', 'Category']
        if not all(col in df.columns for col in required_cols):
            errors.append("Missing required columns.")
        for idx, row in df.iterrows():
            # Date
            if pd.isna(row['Date']):
                errors.append(f"Row {idx+1}: Date is empty.")
            else:
                try:
                    datetime.strptime(str(row['Date']), '%d/%m/%Y')
                except ValueError:
                    errors.append(f"Row {idx+1}: Invalid date format.")
            # Name
            if pd.isna(row['Name']) or not isinstance(row['Name'], str) or len(str(row['Name'])) > 150 or str(row['Name']).replace(' ', '').isalnum() == False:
                errors.append(f"Row {idx+1}: Invalid name.")
            # Type
            if row['Type'] not in ['Needs', 'Wants', 'Savings']:
                errors.append(f"Row {idx+1}: Invalid type.")
            # Amount
            try:
                amt = float(row['Amount'])
                if amt <= 0:
                    errors.append(f"Row {idx+1}: Invalid amount.")
                else:
                    s = str(row['Amount'])
                    if '.' in s:
                        dec = s.split('.')[-1]
                        if len(dec) > 3:
                            errors.append(f"Row {idx+1}: Invalid amount.")
            except Exception:
                errors.append(f"Row {idx+1}: Invalid amount.")
            # Category
            if pd.isna(row['Category']) or not isinstance(row['Category'], str) or len(str(row['Category'])) > 150:
                errors.append(f"Row {idx+1}: Invalid category.")
        if errors:
            return False, errors
        return True, df
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def analyze_data(df, income):
    """Analyze the data and return aggregated results."""
    df['Category'] = df['Category'].str.lower()
    buckets = df.groupby('Type')['Amount'].sum()
    needs = buckets.get('Needs', 0)
    wants = buckets.get('Wants', 0)
    savings = buckets.get('Savings', 0)
    # Top wants categories
    wants_df = df[df['Type'] == 'Wants']
    top_wants = wants_df.groupby('Category')['Amount'].sum().nlargest(5)
    return needs, wants, savings, top_wants