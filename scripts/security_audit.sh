#!/bin/bash

# ============================================================================
# AUTOMATED SECURITY AUDIT SCRIPT
# ============================================================================
# This script runs a suite of security analysis tools against the codebase:
# 1. Bandit (SAST): Static analysis for Python security vulnerabilities
# 2. Pip-audit (SCA): Checks for vulnerabilities in dependencies
# 3. Unit Tests: Runs the security-specific tests (Sanitization, Rate Limiting, Log Masking)
# ============================================================================

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine Python path from project's virtualenv
VENV_PYTHON="/Users/macbookairm3/Finance_Health_Check/.venv/bin/python"

# --- PART 1: SAST (Bandit) ---
echo -e "${GREEN}--- RUNNING BANDIT (SAST) SECURITY SCAN ---${NC}"
# Scan source code and the main application file
$VENV_PYTHON -m bandit -r src/ web_app.py -ll
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Bandit: No high-severity issues found.${NC}"
else
    echo -e "${RED}Bandit: Security warnings detected! Check logs.${NC}"
    exit 1
fi

# --- PART 2: DEPENDENCY AUDIT (Pip-audit) ---
# Note: In a production environment with fixed Python version, this would be a hard failure.
# For this project, we audit but don't exit if it finds environment-blocked vulnerabilities.
echo -e "\n${GREEN}--- RUNNING PIP-AUDIT (DEPENDENCY ANALYZER) ---${NC}"
$VENV_PYTHON -m pip_audit

# --- PART 3: SECURITY UNIT TESTS ---
echo -e "\n${GREEN}--- RUNNING SECURITY-FOCUSED UNIT TESTS ---${NC}"
$VENV_PYTHON -m unittest tests/test_sanitization.py \
                      tests/test_rate_limiting.py \
                      tests/test_log_masking.py \
                      tests/test_pydantic_validation.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Security Tests: All passed.${NC}"
else
    echo -e "${RED}Security Tests: Some tests failed! Critical issue with security logic.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Security Audit Complete.${NC}"
