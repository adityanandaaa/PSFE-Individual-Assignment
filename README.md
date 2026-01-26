# Financial Health Checker

A Python-based application for analyzing personal finances using the 50/30/20 budgeting framework. It validates expense data from Excel files, provides AI-driven insights, and generates professional PDF reports with charts.

## Features

- **Income and Currency Input**: Enter monthly net income and select currency.
- **Excel File Validation**: Upload and validate expense data with detailed error feedback.
- **50/30/20 Analysis**: Automatically categorize and analyze spending against targets.
- **AI Insights**: Get health scores and advice from Gemini AI (with fallback).
- **PDF Reports**: Generate comprehensive reports with bar charts, pie charts, and top categories.
- **Template Download**: Download a sample Excel template for easy data entry.

## Project Structure

```
.
├── app.py                 # Main entry point
├── modules/
│   ├── config.py          # Configuration constants
│   ├── logic.py           # Data validation and analysis
│   ├── ai.py              # AI integration
│   ├── pdf_generator.py   # Chart and PDF generation
│   └── ui.py              # Tkinter UI
├── data/
│   └── currencies.json    # Currency data
├── test_app.py            # Unit tests
├── requirements.md        # Detailed requirements
├── setup.py               # PyInstaller script
└── README.md              # This file
```

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`

## Usage

1. Enter your monthly net income and select currency.
2. Download the template or use your own Excel file with columns: Date, Name, Type, Amount, Category.
3. Upload the file and validate.
4. Analyze and generate the PDF report.

## Requirements

- Python 3.8+
- Libraries: tkinter, pandas, matplotlib, reportlab, google-generativeai
- For packaging: PyInstaller

## Packaging

To create a standalone .exe: `python setup.py`

## License

This project is for educational purposes.
