import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging
from modules.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data
from modules.ai import get_ai_insights
from modules.pdf_generator import generate_pdf
from modules.config import DOWNLOADS_PATH, TEMPLATE_FILE, PDF_FILE

class FinancialHealthChecker:
    """Main GUI application for financial health analysis using 50/30/20 budgeting.
    
    Provides interface for users to:
    - Input monthly income and select currency
    - Download budget template
    - Upload and validate financial data
    - Analyze spending against 50/30/20 targets
    - Generate AI-powered insights
    - Export professional PDF reports
    """
    
    def __init__(self, root):
        """Initialize the application window and components.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Financial Health Checker")
        self.root.geometry("800x600")

        # Load available currencies from data file
        self.currencies = load_currencies()

        # === UI STATE VARIABLES ===
        self.income_var = tk.StringVar()              # Monthly net income input
        self.currency_var = tk.StringVar(value="GBP")  # Selected currency code
        self.file_path = None                          # Path to uploaded Excel file
        self.validated_data = None                     # Validated DataFrame after upload

        # Build the user interface
        self.setup_ui()

    def setup_ui(self):
        """Build the complete user interface layout.
        
        Layout: Left sidebar (income/currency/buttons) | Center (file/analyze buttons) | Right (feedback log)
        """
        # === HEADER SECTION ===
        header = tk.Label(self.root, text="Welcome to the Financial Health Checker", font=("Arial", 16))
        header.pack(pady=10)

        overview = tk.Label(self.root, text="This app uses the 50/30/20 budgeting framework.", font=("Arial", 12))
        overview.pack(pady=5)

        # === LEFT SIDEBAR ===
        sidebar = tk.Frame(self.root)
        sidebar.pack(side=tk.LEFT, padx=20, pady=20)

        # Income input field with real-time validation
        tk.Label(sidebar, text="Monthly Net Income:").pack(anchor=tk.W)
        self.income_entry = tk.Entry(sidebar, textvariable=self.income_var)
        self.income_entry.pack(pady=5)
        self.income_entry.bind("<KeyRelease>", self.validate_income)  # Validate on each keystroke

        # Currency selection dropdown
        tk.Label(sidebar, text="Currency:").pack(anchor=tk.W)
        currency_codes = [c['code'] for c in self.currencies]
        self.currency_combo = ttk.Combobox(sidebar, textvariable=self.currency_var, values=currency_codes, state="readonly")
        self.currency_combo.pack(pady=5)

        # Download template with example data
        tk.Button(sidebar, text="Download Template", command=self.download_template).pack(pady=10)

        # === CENTER PANEL ===
        central = tk.Frame(self.root)
        central.pack(side=tk.LEFT, padx=20, pady=20)

        # File upload button
        self.upload_btn = tk.Button(central, text="Upload Excel File", command=self.upload_file)
        self.upload_btn.pack(pady=10)

        # Analyze button (enabled only after valid file upload)
        self.analyze_btn = tk.Button(central, text="Analyze & Generate PDF", command=self.analyze, state=tk.DISABLED)
        self.analyze_btn.pack(pady=10)

        # === RIGHT FEEDBACK PANEL ===
        self.feedback_text = tk.Text(self.root, height=20, width=40, state=tk.DISABLED)
        self.feedback_text.pack(side=tk.RIGHT, padx=20, pady=20)

    def validate_income(self, event=None):
        """Real-time income validation with visual feedback.
        
        Changes input field background color:
        - Green: valid income (positive number)
        - Red: invalid income (zero, negative, non-numeric)
        """
        income = self.income_var.get()
        if is_valid_income(income):
            self.income_entry.config(bg="lightgreen")  # Valid input
        else:
            self.income_entry.config(bg="lightcoral")  # Invalid input

    def download_template(self):
        """Download a pre-filled Excel template with example transactions.
        
        Creates an example spreadsheet showing the correct format for
        financial data with sample entries demonstrating 50/30/20 allocation.
        """
        import pandas as pd
        
        # === TEMPLATE DATA ===
        # Create sample financial transactions across all categories
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026', '1/4/2026', '1/5/2026', '1/6/2026', '1/7/2026', '1/8/2026', '1/9/2026', '1/10/2026'],
            'Name': ['Rent', 'all you can eat DAIU', 'Investments', 'Electricity Bills', 'Thai Grass', 'NX Bus Pass', 'Aldi Week 1', 'Kebab Rush', 'Stocks Investment', 'Gym Subscription'],
            'Type': ['Needs', 'Wants', 'Savings', 'Needs', 'Wants', 'Needs', 'Needs', 'Wants', 'Savings', 'Needs'],
            'Amount': [520.00, 50.00, 430.00, 4.20, 7.50, 53.00, 16.00, 6.50, 20.00, 18.50],
            'Category': ['Rent', 'Eating Out', 'Gold Investment', 'Electricity', 'Eating Out', 'Bus Pass', 'Groceries', 'Eating Out', 'Stocks', 'Sports']
        }
        df = pd.DataFrame(data)
        
        # Save to user's Downloads folder
        template_path = os.path.join(DOWNLOADS_PATH, TEMPLATE_FILE)
        df.to_excel(template_path, index=False)
        
        # Notify user
        messagebox.showinfo("Template Downloaded", f"Template saved to {template_path}")
        self.log_feedback(f"Template downloaded to: {template_path}")

    def upload_file(self):
        """Open file dialog and validate uploaded Excel file.
        
        Process:
        1. Open file browser filtered to .xlsx files
        2. Validate file structure and data
        3. Enable analyze button if validation succeeds
        4. Log all validation errors if validation fails
        """
        # Open file selection dialog
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        
        if file_path:
            self.file_path = file_path
            self.log_feedback(f"File uploaded: {file_path}")
            
            # Validate the uploaded file
            success, result = validate_file(file_path)
            
            if success:
                # Validation passed - store data and enable analyze
                self.validated_data = result
                self.analyze_btn.config(state=tk.NORMAL)
                self.log_feedback("File validated successfully.")
            else:
                # Validation failed - display all errors
                for error in result:
                    self.log_feedback(error)
                self.analyze_btn.config(state=tk.DISABLED)

    def analyze(self):
        """Execute full financial analysis workflow.
        
        Steps:
        1. Validate income and data are available
        2. Aggregate spending by category (50/30/20 analysis)
        3. Get AI health score and recommendations
        4. Generate comprehensive PDF report
        5. Save to user's Downloads folder
        """
        # Validate prerequisites
        if self.validated_data is None or self.validated_data.empty or not is_valid_income(self.income_var.get()):
            self.log_feedback("No valid data or income to analyze.")
            return
        
        # === PREPARATION ===
        # Get user inputs
        income = float(self.income_var.get())
        currency = self.currency_var.get()
        symbol = get_currency_symbol(self.currencies, currency)

        # === ANALYSIS ===
        # Calculate budget allocation
        needs, wants, savings, top_wants = analyze_data(self.validated_data, income)

        # === AI INSIGHTS ===
        # Get health score and personalized advice
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants.to_dict())

        # === REPORT GENERATION ===
        # Create and save PDF report
        pdf_path = os.path.join(DOWNLOADS_PATH, PDF_FILE)
        generate_pdf(pdf_path, income, symbol, needs, wants, savings, top_wants, score, advice)
        
        # Notify user of successful report generation
        messagebox.showinfo("Success", f"PDF generated: {pdf_path}")
        self.log_feedback(f"PDF generated: {pdf_path}")

    def log_feedback(self, message):
        """Log message to feedback terminal and application log.
        
        Provides real-time user feedback in the GUI while also
        persisting messages to the application log file.
        
        Args:
            message: Text message to log and display
        """
        # Enable text widget temporarily for insertion
        self.feedback_text.config(state=tk.NORMAL)
        # Insert message with newline
        self.feedback_text.insert(tk.END, message + "\n")
        # Disable to prevent user editing
        self.feedback_text.config(state=tk.DISABLED)
        # Scroll to bottom to show latest message
        self.feedback_text.see(tk.END)
        # Also log to application log file
        logging.info(message)