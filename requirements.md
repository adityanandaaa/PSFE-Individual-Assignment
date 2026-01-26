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
The application is implemented in Python with a modular structure for maintainability. The main entry point is `app.py`, which imports from the `modules/` directory. Key modules include:
- `config.py`: Configuration constants and paths.
- `logic.py`: Data validation, loading, and analysis functions.
- `ai.py`: AI insights integration with Gemini 2.0 Flash and fallback.
- `pdf_generator.py`: Chart generation using Matplotlib and PDF creation with ReportLab.
- `ui.py`: Tkinter-based user interface.

Data processing uses pandas and openpyxl for Excel handling. PDF generation uses ReportLab for layout and Matplotlib for chart creation. Input and output are exclusively handled via Excel (.xlsx) and PDF, respectively. The app must be packaged as a standalone .exe file using PyInstaller for easy Windows distribution, ensuring no external dependencies for end-users. Minimum system requirements: Windows 10+, 4GB RAM, 500MB free space. Errors are logged to a local file (e.g., app.log) for debugging. Unit tests are included in test_app.py for validation logic, error handling, and AI fallbacks. All features are designed to meet the assignment requirements, ensuring a professional standard while remaining accessible for a beginner-intermediate developer using Python and tkinter.

## User Stories

- **As an Individual Budgeter**, I want to enter my monthly net income and select my currency so that the analysis reflects my financial context accurately.
- **As an Individual Budgeter**, I want to upload an Excel file of my expenses and receive validation feedback so that I can correct errors before analysis.
- **As an Individual Budgeter**, I want the app to calculate my spending against the 50/30/20 framework and generate a PDF report with charts and AI advice so that I can understand my financial health and make informed decisions.
- **As an Individual Budgeter**, I want the app to process data locally without storing it externally so that my privacy is protected.
- **As an Individual Budgeter**, I want AI to provide a health score and optimization tips so that I can improve my budgeting efficiency.

## Acceptance Criteria

**User Story 1: As an Individual Budgeter, I want to enter my monthly net income and select my currency so that the analysis reflects my financial context accurately.**
- The income input field accepts only positive numeric values greater than zero and rejects negatives or non-numeric input.
- The currency dropdown defaults to GBP and includes options for USD, EUR, IDR, and others from the currencies.json file.
- The selected currency symbol is displayed in the PDF report alongside amounts.

**User Story 2: As an Individual Budgeter, I want to upload an Excel file of my expenses and receive validation feedback so that I can correct errors before analysis.**
- The upload accepts only .xlsx files under 10 MB with up to 500 rows.
- Validation checks for required columns (Date, Name, Type, Amount, Category) and flags errors like invalid dates, empty fields, merged cells, or amounts not greater than zero.
- Feedback terminal displays specific error messages, and the Analyze button remains disabled until all validations pass with no errors.
- Upon any validation failure, a "Re-upload File" button is enabled, and a "Download Template" call-to-action is displayed to guide users in correcting and re-uploading the file.

**User Story 3: As an Individual Budgeter, I want the app to calculate my spending against the 50/30/20 framework and generate a PDF report with charts and AI advice so that I can understand my financial health and make informed decisions.**
- Calculations aggregate expenses into Needs (50%), Wants (30%), and Savings (20%) buckets based on income, and identify the top 5 Wants categories.
- PDF includes three charts: a bar chart with actual spending and target lines, a pie chart with percentages, and a bar chart of top Wants categories, each with headings and descriptions.
- Report generation completes in under 30 seconds and includes AI score and advice, with fallback text if AI fails.
- PDF is saved to the user's Downloads folder.

**User Story 4: As an Individual Budgeter, I want the app to process data locally without storing it externally so that my privacy is protected.**
- All data processing occurs in memory without writing to disk or external servers.
- No user data is retained after the session ends.
- The app runs offline for core features, with AI as an optional enhancement.

**User Story 5: As an Individual Budgeter, I want to receive a financial health score and optimization tips so that I can improve my budgeting efficiency.**
- Health score is calculated using a deterministic mathematical formula based on 50/30/20 targets.
- Score ranges from 0-100% and penalizes only risky behaviors (overspending/under-saving).
- Conservative spending is not penalized; underspending in any category does not reduce the score.
- Weights: Needs 0.2, Wants 0.5, Savings 0.6 to emphasize wants control and savings adequacy.
- Severe penalties: Savings < 0 results in score 0; Needs > 75% results in -10 penalty.
- AI (Gemini) provides personalized optimization tips and actionable recommendations.
- If AI fails, the report includes the calculated health score with generic fallback advice.</content>
<parameter name="filePath">/Users/macbookairm3/new_python_project/requirements.md