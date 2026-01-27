# Finance Health Check 50/30/20

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
- **🤖 AI Advice**: Personalized financial recommendations powered by Google Gemini 2.0 Flash
- **📊 Smart Priority Detection**: AI analyzes deviations and recommends primary/secondary focus areas
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
- Personalized financial recommendations powered by Google Gemini 2.0 Flash
- Comprehensive analysis with 7-section payload:
  * Financial overview and coverage percentage
  * Budget breakdown with percentage allocations
  * Precise deviation analysis from 50/30/20 targets
  * Top spending categories breakdown
  * Health metrics and scoring methodology
  * Primary and secondary focus area recommendations
  * Expected improvement potential
- Structured AI prompts requesting:
  * Current state assessment
  * Key findings (2-3 impactful issues)
  * 3-5 specific, actionable recommendations
  * Expected impact analysis
  * Quick wins for immediate implementation
  * Long-term sustainability strategy

### 6. Download PDF Report
- Click "Generate PDF Report"
- Complete financial health report
- Includes charts, metrics, and advice

## 🎯 Recent Enhancements

### AI Payload Improvements (Latest)
- **7-Section Financial Analysis**: Comprehensive payload with 30+ data fields
- **Smart Priority Detection**: AI determines primary and secondary focus areas based on budget deviations
- **Deviation Analysis**: Precise calculations showing how far each category is from 50/30/20 targets
- **Health Status Categorization**: Automatic categorization as Excellent/Good/Fair based on score
- **Generation Config**: Fine-tuned AI parameters for better response quality
  * Temperature: 0.7 (balanced creativity and consistency)
  * Top P: 0.95 (diverse but focused)
  * Top K: 40 (coherent vocabulary)
  * Max Tokens: 2000 (detailed, comprehensive advice)

### Code Quality Improvements
- **66% File I/O Reduction**: Consolidated file reading operations with caching
- **Enhanced Caching Strategy**: Implemented `@st.cache_data` and `@lru_cache` decorators
- **Comprehensive Documentation**: Added inline comments and docstrings across all modules
- **Dependency Modernization**: Migrated from deprecated `google-generativeai` to `google-genai` v1.60.0
- **Structured Error Handling**: Changed to tuple-based error reporting for better clarity

### Testing Expansion
- **58 Total Tests** (13 new tests for AI enhancements)
- **100% Pass Rate**: All tests passing consistently
- **Comprehensive Coverage**: Logic, AI, PDF, and Streamlit integration testing

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
│   └── Finance Health Check 50_30_20 Templates.xlsx  # Excel template
├── tests/
│   └── test_app.py         # 58 tests (all passing)
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
# Run all 58 tests
.venv/bin/python -m pytest -v tests/test_app.py
# or, after activating the venv
python -m pytest -v tests/test_app.py
```

**Status**: ✅ All 58 tests passing (100%)

### Test Coverage
- **Core Logic Tests** (37 tests)
  * Currency handling and validation
  * Income validation and edge cases
  * File validation with comprehensive error handling
  * 50/30/20 budget analysis
  * Health score calculation
  * PDF report generation

- **AI Enhancement Tests** (13 new tests)
  * Enhanced payload structure validation
  * Budget deviation scenarios
  * Extreme spending patterns
  * Low income handling
  * Health status categorization (Excellent/Good/Fair)
  * Generation config application
  * Priority determination logic (primary focus)
  * Secondary priority logic

- **Streamlit Integration Tests** (8 tests)
  * UI component compatibility
  * Session state management
  * File uploader functionality
  * Download button data preparation

## 🔧 Requirements

- **Python 3.13+**
- **Streamlit 1.28+**
- **google-genai** (v1.60.0+) - Modern Gemini API
- **Virtual environment** (already created)
- **.env file** with `GEMINI_API_KEY` from Google Gemini

### Key Dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.0.0
matplotlib>=3.7.0
reportlab>=4.0.0
google-genai==1.60.0
pydantic>=2.0.0
python-dotenv
pytest
```

## 📝 File Format

Use the provided Excel template with these columns:

| Column | Format | Rules |
|--------|--------|-------|
| **Date** | MM/DD/YYYY or YYYY-MM-DD | Required, valid date |
| **Name** | Text | Required, non-empty |
| **Type** | "Needs", "Wants", or "Savings" | Required, case-insensitive |
| **Amount** | Number (0.00 to 999999.999) | Required, positive, max 3 decimals |
| **Category** | Text | Required, single word or hyphenated |

### Example
```
Date        | Name         | Type    | Amount  | Category
1/15/2026   | Rent         | Needs   | 1500.00 | Rent
1/15/2026   | Groceries    | Needs   | 300.50  | Food
1/20/2026   | Movie Ticket | Wants   | 15.00   | Entertainment
2/1/2026    | Salary Save  | Savings | 1000.00 | Emergency-Fund
```

### Validation Rules
- Dates must be valid calendar dates
- Names cannot be empty
- Type must be exactly: Needs, Wants, or Savings
- Amounts must be positive numbers with max 3 decimal places
- Categories must be single words (hyphens allowed)
- Empty rows are automatically dropped
- File size limited to 5MB

## License

This project is for educational purposes.
