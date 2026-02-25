import unittest
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from src.finance_app.logic import validate_file

class TestPydanticValidation(unittest.TestCase):
    """Test suite for the Pydantic-powered validation logic."""

    def create_excel_file(self, data, headers=None):
        if not headers:
            headers = ['Date', 'Name', 'Type', 'Amount', 'Category']
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in data:
            ws.append(row)
        
        file_stream = BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        return file_stream

    def test_valid_record_pydantic(self):
        # High-integrity record
        data = [['2026-01-01', 'Rent Payment', 'Needs', 1200.00, 'Housing']]
        f = self.create_excel_file(data)
        is_valid, _ = validate_file(f)
        self.assertTrue(is_valid)

    def test_invalid_name_injection_pydantic(self):
        # Names containing potentially malicious chars should fail
        # Pydantic regex: r'^[a-zA-Z0-9\s]+$'
        data = [['2026-01-01', '<script>alert(1)</script>', 'Needs', 1200.00, 'Housing']]
        f = self.create_excel_file(data)
        is_valid, errors = validate_file(f)
        self.assertFalse(is_valid)
        self.assertIn("Invalid name", str(errors))

    def test_invalid_type_pydantic(self):
        # Type must be in [Needs, Wants, Savings]
        data = [['2026-01-01', 'Lunch', 'Leisure', 25.00, 'Food']]
        f = self.create_excel_file(data)
        is_valid, errors = validate_file(f)
        self.assertFalse(is_valid)
        self.assertIn("Invalid type", str(errors))

    def test_negative_amount_pydantic(self):
        # Amount must be GT zero (Pydantic gt=0)
        data = [['2026-01-01', 'Refund', 'Needs', -10.00, 'Misc']]
        f = self.create_excel_file(data)
        is_valid, errors = validate_file(f)
        self.assertFalse(is_valid)
        self.assertIn("Invalid amount", str(errors))

    def test_excessive_decimal_pydantic(self):
        # Should fail if more than 3 decimals (Pydantic custom validator)
        data = [['2026-01-01', 'Gas', 'Needs', 45.1234, 'Travel']]
        f = self.create_excel_file(data)
        is_valid, errors = validate_file(f)
        self.assertFalse(is_valid)
        self.assertIn("Invalid amount", str(errors))

if __name__ == '__main__':
    unittest.main()
