# Project Requirements: Financial Health Checker

## Overview
This document outlines the requirements for a Python-based financial health analysis application designed for individual budgeters. The app uses the 50/30/20 budgeting framework to evaluate personal expenses, providing automated validation, local processing, AI-driven insights, and professional PDF reporting.

## Detailed Requirements

### 1. User Interface (UI) & Navigation Flow
The application features a structured layout to ensure a seamless user journey and a high-quality decision support experience. The header includes a welcome banner and a brief overview of the 50/30/20 budgeting methodology to orient the user. On the left sidebar, users can enter their monthly net income (mandatory, must be greater than zero), select a currency from a dropdown menu (defaulting to GBP), and download a standardized Excel template directly from the project folder. The central control panel allows users to upload the completed Excel file and includes an Analyze & Generate PDF button, which is disabled until a valid file is uploaded. On the right, a feedback terminal displays real-time status logs.

The UI is responsive to different screen sizes (minimum 1024x768) and supports keyboard navigation. The user flow begins with income input and currency confirmation, followed by importing the Excel file (restricted to 10MB and 500 rows). The system validates the data for empty rows, incorrect value types, and merged cells. If validation succeeds, it performs local 50/30/20 calculations and triggers the Gemini AI health check, then generates a professional PDF report. If any validation fails, the process stops, specific error messages are shown, and the user is guided to correct the file using a provided template.

### 2. Advanced Validation & Technical Constraints
The application includes a validation checker to ensure that the logic engine and AI agents receive clean, standardized data. Each column in the Excel input has strict requirements:
- **Date**: Must follow DD/MM/YYYY format and cannot be empty.
- **Name**: Max 150 characters, alphanumeric and spaces only.
- **Type**: Must be strictly 'Needs', 'Wants', or 'Savings'.
- **Amount**: Positive float greater than zero, max 3 decimal places.
- **Category**: Max 150 characters.

The uploader extracts raw values in read-only mode. Security is ensured by processing all data locally and sanitizing inputs to prevent injection or XSS.

### 3. Core Logic & PDF Reporting
The 50/30/20 calculations are performed locally using Python's pandas library. The PDF report includes three charts:
- **Spending vs Targets**: Bar chart comparing actual vs 50/30/20 goals.
- **Budget Breakdown**: Pie chart showing percentage allocation.
- **Top Wants**: Bar chart highlighting the top 5 discretionary spending categories.

The PDF is generated using ReportLab with Matplotlib-generated images embedded. The system is optimized to process files and generate the PDF in under 30 seconds.

### 4. Health Score Calculation & AI Integration
The health score is calculated using a deterministic mathematical formula (0-100) that penalizes only risky behaviors:
- **Needs overspend (>50%)**: Weight 0.2
- **Wants overspend (>30%)**: Weight 0.5
- **Under-saving (<20%)**: Weight 0.6
- **Risk adjustments**: Score = 0 if savings < 0; -10 penalty if needs > 75%.

The Gemini API generates personalized financial advice based on a structured JSON payload. FALLBACK: A calculated health score with generic advice is provided if the AI connection fails.

### 5. Technical Implementation Summary
The application is implemented in Python 3.9+ with a modular structure:
- `config.py`: Configuration and **Environment Protection** (Pydantic validation).
- `logic.py`: Core analysis and **Input Depth Defense** (Pydantic models).
- `ai.py`: **Async** AI insights with Gemini 2.5 Flash and rate limiting.
- `pdf_generator.py`: Chart generation and PDF layout with **Markdown Cleaning**.
- `logging_config.py`: Centralized logging with **PII Masking** and automatic rotation.

**Performance & Security Highlights:**
- **Log Masking**: PII (currency, account digits) is automatically redacted.
- **Async AI calls**: Non-blocking pattern for better scalability.
- **Resource Cleanup**: Try/finally blocks for matplotlib to prevent memory leaks.
- **Sanitization**: `bleach` and `html.escape` protect against XSS/Injection.

**Testing Suite:**
60 comprehensive tests covering:
- 37 core logic tests (calculations, parsing).
- 13 AI integration tests (payloads, priorities).
- 5 Security tests (Sanitization, Throttling, Masking).
- 5 Integrity tests (Pydantic validation).

## User Stories
- **Budgeter**: Wants to input income/currency and get clear 50/30/20 analysis.
- **Budgeter**: Wants validation feedback to fix Excel errors.
- **Budgeter**: Wants a professional PDF report with AI advice.
- **Budgeter**: Wants privacy preserved via local processing.
- **Developer**: Wants comprehensive logging and security auditing.

## Acceptance Criteria
- Income input rejects non-numeric or negative values.
- Selected currency symbol is displayed correctly.
- File upload validates all 5 required columns and respects 10MB limit.
- Health score remains deterministic regardless of AI availability.
- PII is never stored or logged in plaintext.
- All 60 unit tests pass via the automated `security_audit.sh` script.
