import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging
from modules.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data
from modules.ai import get_ai_insights
from modules.pdf_generator import generate_pdf
from modules.config import DOWNLOADS_PATH, TEMPLATE_FILE, PDF_FILE

class FinancialHealthChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Health Checker")
        self.root.geometry("800x600")

        # Load currencies
        self.currencies = load_currencies()

        # Variables
        self.income_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="GBP")
        self.file_path = None
        self.validated_data = None

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Label(self.root, text="Welcome to the Financial Health Checker", font=("Arial", 16))
        header.pack(pady=10)

        overview = tk.Label(self.root, text="This app uses the 50/30/20 budgeting framework.", font=("Arial", 12))
        overview.pack(pady=5)

        # Left sidebar frame
        sidebar = tk.Frame(self.root)
        sidebar.pack(side=tk.LEFT, padx=20, pady=20)

        # Income input
        tk.Label(sidebar, text="Monthly Net Income:").pack(anchor=tk.W)
        self.income_entry = tk.Entry(sidebar, textvariable=self.income_var)
        self.income_entry.pack(pady=5)
        self.income_entry.bind("<KeyRelease>", self.validate_income)

        # Currency selection
        tk.Label(sidebar, text="Currency:").pack(anchor=tk.W)
        currency_codes = [c['code'] for c in self.currencies]
        self.currency_combo = ttk.Combobox(sidebar, textvariable=self.currency_var, values=currency_codes, state="readonly")
        self.currency_combo.pack(pady=5)

        # Download template button
        tk.Button(sidebar, text="Download Template", command=self.download_template).pack(pady=10)

        # Central panel
        central = tk.Frame(self.root)
        central.pack(side=tk.LEFT, padx=20, pady=20)

        # Upload button
        self.upload_btn = tk.Button(central, text="Upload Excel File", command=self.upload_file)
        self.upload_btn.pack(pady=10)

        # Analyze button (disabled initially)
        self.analyze_btn = tk.Button(central, text="Analyze & Generate PDF", command=self.analyze, state=tk.DISABLED)
        self.analyze_btn.pack(pady=10)

        # Right feedback terminal
        self.feedback_text = tk.Text(self.root, height=20, width=40, state=tk.DISABLED)
        self.feedback_text.pack(side=tk.RIGHT, padx=20, pady=20)

    def validate_income(self, event=None):
        income = self.income_var.get()
        if is_valid_income(income):
            self.income_entry.config(bg="lightgreen")
        else:
            self.income_entry.config(bg="lightcoral")

    def download_template(self):
        # Create the specified template with example data
        import pandas as pd
        data = {
            'Date': ['1/1/2026', '1/2/2026', '1/3/2026', '1/4/2026', '1/5/2026', '1/6/2026', '1/7/2026', '1/8/2026', '1/9/2026', '1/10/2026'],
            'Name': ['Rent', 'all you can eat DAIU', 'Investments', 'Electricity Bills', 'Thai Grass', 'NX Bus Pass', 'Aldi Week 1', 'Kebab Rush', 'Stocks Investment', 'Gym Subscription'],
            'Type': ['Needs', 'Wants', 'Savings', 'Needs', 'Wants', 'Needs', 'Needs', 'Wants', 'Savings', 'Needs'],
            'Amount': [520.00, 50.00, 430.00, 4.20, 7.50, 53.00, 16.00, 6.50, 20.00, 18.50],
            'Category': ['Rent', 'Eating Out', 'Gold Investment', 'Electricity', 'Eating Out', 'Bus Pass', 'Groceries', 'Eating Out', 'Stocks', 'Sports']
        }
        df = pd.DataFrame(data)
        template_path = os.path.join(DOWNLOADS_PATH, TEMPLATE_FILE)
        df.to_excel(template_path, index=False)
        messagebox.showinfo("Template Downloaded", f"Template saved to {template_path}")
        self.log_feedback(f"Template downloaded to: {template_path}")

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.file_path = file_path
            self.log_feedback(f"File uploaded: {file_path}")
            success, result = validate_file(file_path)
            if success:
                self.validated_data = result
                self.analyze_btn.config(state=tk.NORMAL)
                self.log_feedback("File validated successfully.")
            else:
                for error in result:
                    self.log_feedback(error)
                self.analyze_btn.config(state=tk.DISABLED)

    def analyze(self):
        if self.validated_data is None or self.validated_data.empty or not is_valid_income(self.income_var.get()):
            self.log_feedback("No valid data or income to analyze.")
            return
        income = float(self.income_var.get())
        currency = self.currency_var.get()
        symbol = get_currency_symbol(self.currencies, currency)

        needs, wants, savings, top_wants = analyze_data(self.validated_data, income)

        # AI
        score, advice = get_ai_insights(income, needs, wants, savings, top_wants.to_dict())

        # Generate PDF
        pdf_path = os.path.join(DOWNLOADS_PATH, PDF_FILE)
        generate_pdf(pdf_path, income, symbol, needs, wants, savings, top_wants, score, advice)
        messagebox.showinfo("Success", f"PDF generated: {pdf_path}")
        self.log_feedback(f"PDF generated: {pdf_path}")

    def log_feedback(self, message):
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.insert(tk.END, message + "\n")
        self.feedback_text.config(state=tk.DISABLED)
        self.feedback_text.see(tk.END)
        logging.info(message)