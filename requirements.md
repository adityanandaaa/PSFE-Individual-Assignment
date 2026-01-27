# Project Requirements: Financial Health Checker

## Overview
This document outlines the requirements for a Python-based financial health analysis application designed for individual budgeters. The app uses the 50/30/20 budgeting framework to evaluate personal expenses, providing automated validation, local processing, AI-driven insights, and professional PDF reporting.

## Detailed Requirements

### 1. User Interface (UI) & Navigation Flow
The application features a structured layout to ensure a seamless user journey and a high-quality decision support experience. The header includes a welcome banner and a brief overview of the 50/30/20 budgeting methodology to orient the user. On the left sidebar, users can enter their monthly net income (mandatory, must be greater than zero), select a currency from a dropdown menu (defaulting to GBP), and download a standardized Excel template directly from the project folder. The central control panel allows users to upload the completed Excel file and includes an Analyze & Generate PDF button, which is disabled until a valid file is uploaded. On the right, a feedback terminal displays real-time status logs such as "Upload Success," validation progress, or a list of errors if the file fails checks.

The UI is responsive to different screen sizes (minimum 1024x768) and supports keyboard navigation for accessibility. The user flow begins with income input and currency confirmation, followed by importing the Excel file (restricted to 10MB and 500 rows). The system validates the data for empty rows, incorrect value types, and merged cells. If validation succeeds, it performs local 50/30/20 calculations and triggers the dual-AI health check, then generates a professional PDF report. If any validation fails (even a single error), the process stops, the feedback terminal displays a list of specific errors (e.g., "Invalid date format in row 5"), the Analyze button remains disabled, and a "Re-upload File" button is enabled with a call-to-action prompt: "Please correct the errors in your Excel file and re-upload, or download the template again for guidance." The "Download Template" button is also prominently displayed as a CTA to assist users in fixing issues. No partial processing is allowed; the entire file must be error-free. No visualizations are shown directly within the UI; the PDF is the only output medium.

### 2. Advanced Validation & Technical Constraints
The application includes a validation checker to ensure that the logic engine and AI agents receive clean, standardized data. Each column in the Excel input has strict requirements: the Date must follow DD/MM/YYYY format and cannot be empty; the Name column allows up to 150 characters and cannot consist solely of numbers or special characters; Type must be one of the enumerated options—Needs, Wants, or Savings; Amount must be a positive float greater than zero with a maximum of three decimal places; and Categories support up to 150 characters with non-case-sensitive handling (e.g., "Food" and "food" are treated identically).

The uploader extracts raw values in read-only mode, ignoring formulas and flagging merged cells as errors to prevent data misalignment. Security is ensured by processing all data locally, without storing it externally.

### 3. Core Logic & PDF Reporting
The system focuses on data processing and professional documentation rather than on-screen visualization. The 50/30/20 calculations are performed locally using Python's pandas library, and the report generation remains functional even if the AI connection fails. The PDF report is the exclusive output and includes three charts: a bar chart comparing actual spending in Needs, Wants, and Savings against the 50/30/20 targets (with lines for targets); a pie chart showing the percentage breakdown of expenses across Needs, Wants, and Savings (distinct colors: Needs-blue, Wants-red, Savings-green; with percentages); and a bar chart highlighting the top 5 spending categories within the "Wants" bucket. Each chart section has a heading (e.g., "Spending vs Targets") and a descriptive paragraph explaining the visualization. The PDF is generated using ReportLab with Matplotlib-generated images embedded. The system is optimized to process files and generate the PDF in under 30 seconds on standard 8GB RAM hardware.

### 4. Health Score Calculation & AI Integration
The health score is calculated using a deterministic mathematical formula based on the 50/30/20 framework. This ensures consistent, transparent scoring independent of external AI services.

**Health Score Formula:**
- Calculate ratios: n = N/I, w = W/I, s = S/I
- Directional deviations (penalize only risky behavior):
  - Dn = max(0, n - 0.5) - Needs overspend
  - Dw = max(0, w - 0.3) - Wants overspend
  - Ds = max(0, 0.2 - s) - Under-saving
- Weighted score: Score = 100 × (1 - (0.2×Dn + 0.5×Dw + 0.6×Ds))
- Risk adjustments:
  - If savings < 0: Score = 0 (financial danger)
  - If needs > 75%: Score -= 10 (extreme overspend)
- Final: Score = max(0, min(100, Score))

Weights prioritize wants control (0.5) and savings adequacy (0.6), with lower weight on needs (0.2). Conservative spending (under-allocation) is not penalized.

The Gemini API is used only for generating personalized financial advice and recommendations, not for scoring. The AI receives a structured JSON payload with financial data and provides actionable optimization tips. If the AI connection fails, the report includes the calculated health score with fallback generic advice.

### 5. Technical Implementation Summary
The application is implemented in Python 3.13+ with a modular structure for maintainability. The main entry point is `web_app.py` (Streamlit web application), which imports from the `src/finance_app/` directory. Key modules include:
- `config.py`: Configuration constants and paths.
- `logic.py`: Data validation, loading, and analysis functions with caching optimizations.
- `ai.py`: AI insights integration with Gemini 2.0 Flash, enhanced payload with 7-section framework and priority detection, and fallback templates.
- `pdf_generator.py`: Chart generation using Matplotlib and PDF creation with ReportLab.
- `logging_config.py`: Centralized logging configuration with automatic rotation (10MB max, 5 backups).

Data processing uses pandas and openpyxl for Excel handling. PDF generation uses ReportLab for layout and Matplotlib for chart creation. Input and output are exclusively handled via Excel (.xlsx) and PDF, respectively. The app runs as a Streamlit web application on localhost:8501, requiring only Python 3.13+ with the dependencies listed in requirements.txt (google-genai v1.60.0 for modern Gemini API). All processing occurs locally on the user's machine with no external server deployment.

**Performance Optimizations:**
- 66% file I/O reduction through consolidated validation and unified reading process.
- Streamlit caching (@st.cache_data) for UI components and currency data.
- Function-level caching (@lru_cache) for expensive operations (currency loading).
- Automatic log rotation with separate file (INFO level) and console (WARNING level) handlers.
- Matplotlib figure cleanup to prevent memory leaks.

**AI Enhancements:**
- Enhanced payload structure: 7 sections (user_profile, financial_overview, budget_breakdown, deviation_analysis, top_wants_categories, health_metrics, priority_areas) with 30+ data fields.
- Priority detection functions for identifying primary and secondary focus areas based on budget deviations.
- Generation config: temperature 0.7, top_p 0.95, top_k 40, max_tokens 2000 for balanced and detailed responses.
- Comprehensive prompt requesting current state assessment, key findings, 3-5 recommendations, impact analysis, quick wins, and long-term strategy.

**Logging & Monitoring:**
- Comprehensive logging configuration with RotatingFileHandler and ConsoleHandler.
- File logging: INFO+ messages to app.log with automatic rotation at 10MB.
- Console logging: WARNING+ only to minimize noise during app execution.
- Complete LOGGING.md documentation with usage examples and configuration options.

Minimum system requirements: 4GB RAM, 500MB free space. Errors are logged to a local file (app.log) for debugging with automatic rotation. Unit tests are included in test_app.py (58 comprehensive tests covering validation logic, AI fallbacks, error handling, and integration). The test suite includes:
- 37 core logic tests for currency handling, income validation, file processing, and health score calculation.
- 13 AI enhancement tests for payload structure, priority detection, and generation configuration.
- 8 Streamlit integration tests for UI behavior and session state management.

All features are designed to meet the assignment requirements, ensuring a professional standard while remaining accessible for a beginner-intermediate developer using Python.

## User Stories

- **As an Individual Budgeter**, I want to enter my monthly net income and select my currency so that the analysis reflects my financial context accurately.
- **As an Individual Budgeter**, I want to upload an Excel file of my expenses and receive validation feedback so that I can correct errors before analysis.
- **As an Individual Budgeter**, I want the app to calculate my spending against the 50/30/20 framework and generate a PDF report with charts, a deterministic health score, and AI advice so that I can understand my financial health and make informed decisions.
- **As an Individual Budgeter**, I want the app to process data locally without storing it externally so that my privacy is protected.
- **As an Individual Budgeter**, I want a transparent, mathematical health score (not dependent on external AI) along with personalized AI optimization tips that identify my primary and secondary budget focus areas so that I can understand why I received my score and how to improve.
- **As a Developer/Administrator**, I want comprehensive logging with automatic rotation so that I can monitor app performance, debug issues, and maintain the application effectively.

## Acceptance Criteria

**User Story 1: As an Individual Budgeter, I want to enter my monthly net income and select my currency so that the analysis reflects my financial context accurately.**
- The income input field accepts only positive numeric values greater than zero and rejects negatives or non-numeric input.
- The currency dropdown defaults to GBP and includes options for USD, EUR, IDR, and others from the currencies.json file.
- The selected currency symbol is displayed in the PDF report alongside amounts.
- Real-time validation feedback shows green for valid income and red for invalid input.

**User Story 2: As an Individual Budgeter, I want to upload an Excel file of my expenses and receive validation feedback so that I can correct errors before analysis.**
- The upload accepts only .xlsx files under 10 MB with up to 500 rows.
- Validation checks for required columns (Date, Name, Type, Amount, Category) and flags errors like invalid dates, empty fields, merged cells, or amounts not greater than zero.
- Feedback terminal displays specific error messages, and the Analyze button remains disabled until all validations pass with no errors.
- Upon any validation failure, a "Re-upload File" button is enabled, and a "Download Template" call-to-action is displayed to guide users in correcting and re-uploading the file.

**User Story 3: As an Individual Budgeter, I want the app to calculate my spending against the 50/30/20 framework and generate a PDF report with charts, health score, and advice so that I can understand my financial health and make informed decisions.**
- Calculations aggregate expenses into Needs (50%), Wants (30%), and Savings (20%) buckets based on income, and identify the top 5 Wants categories.
- PDF includes three charts: a bar chart with actual spending and target lines, a pie chart with percentages, and a bar chart of top Wants categories, each with headings and descriptions.
- PDF displays the calculated health score (0-100) prominently with explanation of what the score means.
- Report generation completes in under 30 seconds and includes AI-generated personalized advice.
- PDF is saved to the user's Downloads folder with a unique timestamp-based filename.

**User Story 4: As an Individual Budgeter, I want the app to process data locally without storing it externally so that my privacy is protected.**
- All data processing occurs in memory without writing to disk or external servers.
- No user data is retained after the session ends.
- The app runs completely offline for health score calculation and core features.
- AI integration is optional; core functionality works without Gemini API connection.

**User Story 5: As an Individual Budgeter, I want a transparent, mathematical health score along with personalized AI optimization tips that identify my primary and secondary budget focus areas so that I can understand why I received my score and how to improve.**
- Health score is calculated using a deterministic mathematical formula independent of AI services.
- Score ranges from 0-100 and penalizes only risky behaviors: needs overspend (weight 0.2), wants overspend (weight 0.5), and under-saving (weight 0.6).
- Conservative spending (underspending in any category) is not penalized; perfect score is still 100 even with lower spending.
- Severe penalties apply: Savings < 0 results in score 0 (financial danger); Needs > 75% results in -10 penalty.
- AI (Gemini) payload includes comprehensive financial context: user profile, financial overview, budget breakdown with deviations, top 5 wants categories, health metrics, and identified primary/secondary priority areas.
- Priority detection analyzes budget deviations to recommend focus areas: primary priority (reduce needs overspend, reduce wants overspend, or increase savings) and secondary priority (address secondary budget issues).
- AI provides personalized optimization tips for reducing wants and increasing savings with impact analysis, quick wins, and long-term strategy.
- If AI fails, the report includes the calculated health score with generic fallback advice based on the 50/30/20 analysis.

**User Story 6: As a Developer/Administrator, I want comprehensive logging with automatic rotation so that I can monitor app performance, debug issues, and maintain the application effectively.**
- Logging configuration provides separate handlers for file and console output with configurable log levels.
- File logging writes to app.log with INFO level, capturing detailed application events and errors.
- Console logging displays WARNING level and above, minimizing noise during normal app operation.
- Automatic log rotation triggers at 10MB file size with 5 backup files maintained for historical reference.
- Log entries include timestamps (YYYY-MM-DD HH:MM:SS), log level, and descriptive messages for easy debugging.
- Logging configuration can be dynamically adjusted at runtime via set_log_level() function.
- Module-level loggers via get_logger(__name__) provide consistent logging across all application modules.
- LOGGING.md documentation provides configuration examples and best practices for development and production environments.</content>
<parameter name="filePath">/Users/macbookairm3/new_python_project/requirements.md