# Finance Check 50/30/20

A web application for analyzing personal finances using the 50/30/20 budgeting framework. Built with Streamlit for easy localhost deployment. It validates expense data from Excel files, provides AI-driven insights, and generates professional PDF reports with charts.

## Features

- **Income and Currency Input**: Enter monthly net income and select currency.
- **Excel File Validation**: Upload and validate expense data with detailed error feedback.
- **50/30/20 Analysis**: Automatically categorize and analyze spending against targets.
- **Health Score**: Get a deterministic financial health score (0-100) based on mathematical formula, independent of AI services.
- **AI Insights**: Get personalized financial advice from Gemini AI (with fallback).
- **PDF Reports**: Generate comprehensive reports with bar charts, pie charts, top categories, health score, and advice.
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
3. Create a `.env` file with your Google Gemini API key:
   ```
## Running the App

The web app runs locally at `http://localhost:8501`:

```bash
streamlit run web_app.py
```

Then open your browser to the provided URL.

## Usage

1. Enter your monthly net income and select currency.
2. Download the template or use your own Excel file with columns: Date, Name, Type, Amount, Category.
3. Upload the file and analyze.
4. View your 50/30/20 breakdown, health score, and AI advice.
5. Download the PDF report for record-keeping.

## Requirements

- Python 3.8+
- Libraries: streamlit, pandas, matplotlib, reportlab, google-generativeai
- Google Gemini API key (free tier available)

## Packaging

To create a standalone .exe: `python setup.py`

## License

This project is for educational purposes.
