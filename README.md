# Finance Health Check 50/30/20

A modern web application for analyzing personal finances using the 50/30/20 budgeting framework. Built with Streamlit - no .exe installation needed, just run a simple command.

> **📦 Note on Submission**: The `.venv` folder (378 MB virtual environment) is not included in the submission package due to size constraints. The complete project with virtual environment is available on the [GitHub repository](https://github.com/adityanandaaa/PSFE-Individual-Assignment). You can recreate the environment using `python -m venv .venv` and `pip install -r requirements.txt`.

## 🚀 Quick Start (3 Steps)

```bash
# 1. Navigate to project
cd /Users/macbookairm3/Finance_Health_Check

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
- **🤖 AI Advice**: Personalized financial recommendations powered by Google Gemini 2.5 Flash
- **📊 Smart Priority Detection**: AI analyzes deviations and recommends primary/secondary focus areas
- **📈 Visualizations**: Interactive charts showing budget breakdown
- **📥 PDF Reports**: Download comprehensive financial health reports
- **📋 Comprehensive Logging**: Automatic log rotation with file and console handlers
- **🔒 Security Hardening**: 
  - **Pydantic Validation**: Strict schema enforcement for all data inputs.
  - **Environment Protection**: Automatic verification of API keys and configurations.
  - **Session Management**: 30-minute inactivity timeouts for privacy.
  - **AI Circuit Breaker**: Intelligent rate-limit handling for Gemini API.
  - **SAST & SCA Audited**: Regularly scanned with Bandit and Pip-audit.

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
- Personalized financial recommendations powered by Google Gemini 2.5 Flash
- **Async API Integration**: Non-blocking async/await pattern for better scalability
- **Currency-Aware Advice**: AI receives user's selected currency and provides localized recommendations
- Comprehensive analysis with 7-section payload:
  * Financial overview and coverage percentage
  * Budget breakdown with percentage allocations
  * Precise deviation analysis from 50/30/20 targets
  * Top spending categories breakdown (limited to top 3 for efficiency)
  * Health metrics and scoring methodology
  * Primary and secondary focus area recommendations
  * Expected improvement potential
- Structured AI prompts requesting:
  * Current state assessment
  * 3 specific recommendations with quantified impact
  * 1 quick win and 1 long-term habit
  * Clear headers and bullets for readability
- **Markdown Cleaning**: AI responses automatically cleaned before PDF generation

### 6. Download PDF Report
- Click "Generate PDF Report"
- Complete financial health report
- Includes charts, metrics, and advice

## 🎯 Recent Enhancements

### Production Readiness Improvements (Latest)
- **Async AI Integration**: Converted to async/await pattern using `client.aio.models.generate_content`
- **Currency Context**: AI now receives user's selected currency for localized advice
- **Markdown Cleaning**: Automatic removal of markdown formatting (###, **, *) from AI responses before PDF generation
- **UI Date Formatting**: Preview table displays dates in dd/mm/yyyy format for better readability
- **Total Expenses Display**: Real-time calculation shown after file validation
- **Critical Production Fixes**:
  * Specific exception handling (replaced broad Exception catches)
  * Matplotlib figure cleanup (try/finally blocks to prevent memory leaks)
  * Secure logging (no sensitive financial data in logs)

### Logging Configuration
- **Comprehensive Logging System**: Centralized logging configuration module
- **File Logging**: INFO+ messages saved to `app.log` with automatic rotation
- **Console Logging**: Only WARNING+ to terminal for minimal noise
- **Auto-Rotation**: Logs rotate at 10MB with 5 backup files maintained
- **Documentation**: Complete LOGGING.md guide with usage examples and best practices
- **Module Integration**: All modules (ai.py, logic.py) use module-level loggers

### Bug Fixes
- **Fixed set_page_config() Error**: Moved to first Streamlit command in web_app.py
- **Fixed error_rows Variable**: Initialize before conditional block to prevent NameError
- **Fixed Duplicate Display**: Removed duplicate total expenses calculation
- **Improved Code Structure**: Better separation of concerns in initialization

### AI Payload Improvements
- **Async API Pattern**: Non-blocking async/await for better concurrency
- **7-Section Financial Analysis**: Comprehensive payload with 30+ data fields
- **Smart Priority Detection**: AI determines primary and secondary focus areas based on budget deviations
- **Deviation Analysis**: Precise calculations showing how far each category is from 50/30/20 targets
- **Health Status Categorization**: Automatic categorization as Excellent/Good/Fair based on score
- **Currency Context**: User's selected currency included in payload and prompt
- **Compact Prompt**: Reduced input tokens with JSON minification (separators=",",":")
- **Top Wants Optimization**: Limited to top 3 categories to reduce token usage
- **Markdown Support**: AI can use markdown formatting (automatically cleaned for PDF)

### Code Quality Improvements
- **66% File I/O Reduction**: Consolidated file reading operations with caching
- **Enhanced Caching Strategy**: Implemented `@st.cache_data` and `@lru_cache` decorators
- **Comprehensive Documentation**: Added inline comments and docstrings across all modules
- **Dependency Modernization**: Migrated from deprecated `google-generativeai` to `google-genai` v1.60.0
- **Structured Error Handling**: Changed to tuple-based error reporting for better clarity

### Testing Expansion
- **121 Total Tests** (70 core + 2 performance + 9 rate limiting + 39 sanitization + 1 Pydantic/Environment)
- **100% Pass Rate**: All tests passing consistently
- **Comprehensive Coverage**: Logic, AI, PDF, Streamlit integration, performance, security, and Pydantic validation
- **Performance Tests**: Load time (cold/warm) and feature runtime monitoring
- **Rate Limiting Tests**: Throttling, exponential backoff, and **AI Circuit Breaker** verification
- **Sanitization Tests**: XSS/injection prevention across 39 test cases

### 🔐 Security Enhancements (Latest)
- **Input Depth Defense (Pydantic v2)**: 
  * Strict schema enforcement for all data models using Pydantic.
  * Validation of all transactions (date formats, types, amounts).
  * Environment protection ensuring all required API keys and settings are valid before startup.
- **AI Circuit Breaker**:
  * Persistent tracking of API quota exhaustion (`RESOURCE_EXHAUSTED`).
  * Stops redundant retries once a limit is hit, preserving test speed and system stability.
- **Input Sanitization & XSS Prevention**:
  * `sanitizer.py` module removes HTML/JavaScript from all user inputs
  * Category names sanitized before PDF display
  * File names cleaned to prevent path traversal attacks
  * Currency symbols validated to prevent injection
  * 39 comprehensive tests covering XSS vectors, SQL injection, path traversal
  * Uses `bleach` library + HTML escaping for defense-in-depth
  * Protects: Excel file names, category names, AI advice, currency symbols, amounts
- **Rate Limiting & Throttling**:
  * Max 10 API calls per minute (prevents resource exhaustion)
  * Exponential backoff retry mechanism (1s → 2s → 4s)
  * Max 3 retry attempts per API call
  * File upload limit: 50 MB max
- **Secure Credentials**:
  * API keys stored in `.env` (never in code)
  * `.env` in `.gitignore` (not committed to git)
  * Logging only shows first 10 chars of API key
  * Uses `os.getenv()` for secure environment variable loading
- **Error Handling & Exception Management**:
  * 15+ try-catch blocks with specific exception types
  * Graceful fallback when API unavailable
  * Error logging doesn't expose financial data
- **Data Validation & Input Sanitization**:
  * Excel file validation (dates, amounts, categories)
  * Income validation (positive numbers only)
  * Currency whitelist (84 approved countries)
  * Type validation (Needs/Wants/Savings only)
  * User input sanitized before display/storage
- **File Handling Security**:
  * PDF generation with resource cleanup (try-finally blocks)
  * Memory leak prevention via `plt.close()`
  * Temporary files handled safely
- **Logging & Auditing**:
  * Centralized logging configuration (RotatingFileHandler)
  * 10 MB max per log file, 5 backups maintained
  * WARNING+ to console, INFO+ to file
  * No sensitive data logged

### Current Status (Feb 25, 2026)
✅ **Production Ready** - All major features implemented and tested
- App is stable with **121 total tests** (all passing)
- Security hardened with Pydantic validation, AI circuit breaker, input sanitization, and PII masking.
- Performance monitored with load time tests
- 100% error handling coverage across all modules
- XSS/Injection attacks prevented with comprehensive sanitization
- Ready for deployment with proper environment setup

## 📁 Project Structure

```
├── web_app.py              # Main web application
├── src/
│   └── finance_app/        # Core package
│       ├── logic.py        # Financial calculations & Validation integration
│       ├── ai.py           # AI insights (with circuit breaker)
│       ├── models.py       # Pydantic data models (NEW: Input Depth Defense)
│       ├── pdf_generator.py # PDF reports (sanitized output)
│       ├── config.py       # Configuration & Environment Protection
│       ├── logging_config.py # Logging setup with PII masking
│       ├── rate_limiting.py # Rate limiting & AI Circuit Breaker (UPDATED)
│       └── sanitizer.py    # XSS/Injection prevention
├── data/
│   ├── currencies.json     # 84 currencies
│   └── Finance Health Check 50_30_20 Templates.xlsx  # Excel template
├── tests/
│   ├── test_app.py         # 70 core tests
│   ├── test_rate_limiting.py # 9 rate limiting tests
│   ├── test_performance.py # 2 performance tests
│   ├── test_sanitization.py # 39 sanitization tests
│   └── test_pydantic_validation.py # Pydantic schema tests (NEW)
├── legacy/                 # Old desktop app code
├── requirements.txt        # Dependencies
├── requirements-frozen.txt # Exact reproducible environment (NEW)
└── .env                    # API configuration
```

## 📊 Templates & Sample Results

### Excel Template
A complete Excel template is provided: **`data/Finance Health Check 50_30_20 Templates.xlsx`**

This template includes:
- Pre-formatted columns (Date, Name, Type, Amount, Category)
- Example data showing proper formatting
- Instructions sheet with column requirements
- Multiple example transactions covering Needs, Wants, and Savings categories

**How to Use**:
1. Download the template from `data/Finance Health Check 50_30_20 Templates.xlsx`
2. Add your transactions following the example format
3. Save as Excel file (.xlsx)
4. Upload to the web app

### Sample Analysis Results

**Check `result_examples/` folder for real sample outputs:**

1. **`[AI Advice] financial_report_20260128_112733.pdf`**
   - Live Gemini AI-powered recommendations
   - Real analysis with AI-generated insights
   - Personalized financial advice and priority areas
   - Shows what output looks like with working API

2. **`[Fallback Advice] financial_report_20260128_112138.pdf`**
   - Fallback recommendations (when API unavailable)
   - Deterministic, rule-based financial guidance
   - Same professional formatting and charts
   - Shows app always delivers value, with or without AI

When you upload your spending data, the app generates:

**Budget Breakdown Analysis**
- Automatic categorization of spending into Needs (50%), Wants (30%), Savings (20%)
- Percentage of income allocated to each category
- Identification of deviations from optimal 50/30/20 targets

**Financial Health Score (0-100)**
- **90-100**: Excellent - Perfect budget alignment
- **70-89**: Good - Minor optimizations needed
- **50-69**: Fair - Significant rebalancing recommended
- **0-49**: Poor - Major changes required

**AI-Generated Recommendations** (when API available)
- Current financial state assessment
- 3 specific, quantified recommendations for improvement
- 1 quick win (immediate action) and 1 long-term habit
- Currency-aware advice using your selected currency

**Fallback Recommendations** (when API unavailable)
- Intelligent, deterministic financial guidance
- Adapts to your current financial health score
- 10 different recommendation templates for variety
- Ensures users always get valuable feedback

**Priority Focus Areas**
- **Primary Focus**: The single biggest area to optimize
- **Secondary Focus**: The second most important area
- **Improvement Potential**: Estimated income savings achievable

**Visual Charts**
- Pie chart showing budget breakdown
- Bar chart comparing current vs. target percentages
- Category spending breakdown visualization

**PDF Report**
- Complete one-page summary with all analysis
- Embedded charts and visualizations
- AI or fallback advice formatted for easy reading
- Ready to save and share

## 📦 Installation

Already done! Virtual environment and dependencies are set up. Just run:
```bash
streamlit run web_app.py
```

## 🧪 Testing

```bash
# Run all 121 tests
.venv/bin/python -m unittest discover tests

# Or run specific test suites
python -m unittest tests/test_app.py
python -m unittest tests/test_pydantic_validation.py
```

**Status**: ✅ All 121 tests passing (100%)

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

- **Performance Tests** (2 tests)
  * Website load time (cold cache: 8s max, warm cache: 3s max)
  * Feature runtime measurement (1.5s max)

- **Rate Limiting & Security Tests** (9 tests)
  * Rate limiter functionality (within/exceeds limit)
  * Exponential backoff retry mechanism
  * File upload validation
  * Status reporting

- **Input Sanitization Tests** (39 tests) (NEW)
  * XSS/HTML tag removal (multiple vectors)
  * JavaScript/injection attack prevention
  * Path traversal protection
  * HTML entity escaping
  * File name sanitization
  * Category name sanitization
  * Currency symbol validation
  * Amount string sanitization
  * Real-world category name handling

## 🛡️ Security Features

This application implements multi-layered security protections. Detailed security configurations and vulnerability reporting can be found in [SECURITY.md](SECURITY.md).

- **Data Sanitization**: XSS/Injection prevention for all inputs (`bleach`).
- **Input Depth Defense**: Strict schema validation using Pydantic models.
- **Log Masking**: Automatic PII redaction in application logs.
- **Session Security**: Automatic 30-minute inactivity timeout.
- **AI Throttling**: Rate limiting and exponential backoff for Gemini API.
- **Continuous Auditing**: Integrated `bandit` (SAST) and `pip-audit`.

## 🔍 Running Security Audits
A comprehensive security audit script is provided to verify the codebase's integrity:

```bash
chmod +x scripts/security_audit.sh
./scripts/security_audit.sh
```

This runs:
1. **Bandit (SAST)**: Static code analysis for security vulnerabilities.
2. **Pip-audit**: Dependency vulnerability scanning.
3. **Security Logic Tests**: Runs all unit tests specifically designed for sanitization, rate-limiting, and PII protection.

## 🔧 Requirements

- **Python 3.9+** (Current implementation tested on 3.9.6)
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
bleach>=6.0.0           # NEW: XSS/Injection prevention
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
