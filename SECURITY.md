# Security Policy

## Reporting a Vulnerability

We take the security of this project seriously. If you find a security vulnerability, please report it immediately.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report vulnerabilities by contacting the project maintainer directly at:
- Email: [developer-email-here@example.com]

We will acknowledge receipt of your vulnerability report within 48 hours and provide a timeline for a fix within 1 week for critical or high-severity issues.

## Supported Versions

Only the latest `main` branch is currently supported for security updates.

## Security Features Implemented

The **Finance Health Check** application has the following security safeguards in place:

1.  **SAST & SCA**: Regular static analysis (Bandit) and dependency auditing (Pip-audit).
2.  **Input Depth Defense**: Pydantic models for all incoming financial data.
3.  **Sanitization**: All user-provided strings (categories, names, etc.) are sanitized against XSS.
4.  **Log Masking**: PII like account digits and currency amounts are masked in logs.
5.  **Rate Limiting**: Throttling for external AI API calls.
6.  **Session Security**: Automatic 30-minute inactivity timeout for in-memory data.
7.  **Environment Protection**: Validation schemas for sensitive environment settings.
