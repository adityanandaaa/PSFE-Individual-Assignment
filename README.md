# Finance Check 50/30/20

A modern web application for analyzing personal finances using the 50/30/20 budgeting framework. Built with Streamlit - no .exe installation needed, just run a simple command.

## 🚀 Quick Start (3 Steps)

```bash
# 1. Navigate to project
cd /Users/macbookairm3/new_python_project

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Run the app
streamlit run web_app.py
```

Opens at: **http://localhost:8501**

## ✨ Features

- **💱 84 Currencies**: Select from 84 countries
- **📁 File Upload**: Validate Excel files with your spending data
- **📊 Budget Analysis**: Automatic Needs/Wants/Savings breakdown
- **💪 Health Score**: Financial health score (0-100) with color coding
- **🤖 AI Advice**: Personalized financial recommendations from Google Gemini
- **📈 Visualizations**: Interactive charts showing budget breakdown
- **📥 PDF Reports**: Download comprehensive financial health reports

## 📋 How to Use

### 1. Select Currency
- Click dropdown → choose from 84 currencies
- Format: "CODE - Symbol" (e.g., USD - $)

### 2. Upload Excel File
- Click "Upload Excel File"
- Select your spending data
- App validates automatically

### 3. Review Analysis
Shows:
- **Needs (50%)**: Essential expenses
- **Wants (30%)**: Discretionary spending  
- **Savings (20%)**: Money to save

### 4. Check Health Score
- Score from 0-100
- Color-coded (Poor/Fair/Good/Excellent)
- See % of income in each category

### 5. Get AI Advice
- Personalized financial recommendations
- Based on your budget data
- Actionable insights

### 6. Download PDF Report
- Click "Generate PDF Report"
- Complete financial health report
- Includes charts, metrics, and advice

## 📁 Project Structure

```
├── web_app.py              # Main web application
├── src/
│   └── finance_app/        # Core package
│       ├── logic.py        # Financial calculations
│       ├── ai.py           # AI insights
│       ├── pdf_generator.py # PDF reports
│       └── config.py       # Configuration
├── data/
│   ├── currencies.json     # 84 currencies
│   └── Finance Check 50_30_20 Templates.xlsx  # Excel template
├── tests/
│   └── test_app.py         # 45 tests (all passing)
├── legacy/                 # Old desktop app code
├── requirements.txt        # Dependencies
├── pyproject.toml          # Package configuration
└── .env                    # API configuration
```

## 📦 Installation

Already done! Virtual environment and dependencies are set up. Just run:
```bash
streamlit run web_app.py
```

## 🧪 Testing

```bash
# Run all 45 tests
.venv/bin/python -m pytest -v tests/test_app.py
# or, after activating the venv
python -m pytest -v tests/test_app.py
```

**Status**: ✅ All 45 tests passing (100%)

## 🔧 Requirements

- **Python 3.9+**
- **Streamlit 1.28+**
- **Virtual environment** (already created)
- **.env file** with Google Gemini API key

## 📝 File Format

Use the provided Excel template. Include:
- Spending categories in rows
- Amounts as numbers (not text)
- Consistent date ranges
- All major expense categories
2. Download the template or use your own Excel file with columns: Date, Name, Type, Amount, Category.
3. Upload the file and analyze.
4. View your 50/30/20 breakdown, health score, and AI advice.
5. Download the PDF report for record-keeping.

## Requirements

- Python 3.8+
- Libraries: streamlit, pandas, matplotlib, reportlab, google-generativeai
- Google Gemini API key (free tier available)

## License

This project is for educational purposes.
