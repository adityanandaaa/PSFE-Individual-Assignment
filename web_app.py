# ============================================================================
# FINANCE HEALTH CHECK 50/30/20 WEB APPLICATION
# ============================================================================
# A Streamlit-based web application for analyzing personal finances using the
# 50/30/20 budgeting rule (50% needs, 30% wants, 20% savings).
# ============================================================================

import streamlit as st

# ============================================================================
# PAGE CONFIGURATION (MUST BE FIRST STREAMLIT COMMAND)
# ============================================================================
# Configure Streamlit page settings before any other Streamlit commands
st.set_page_config(
    page_title="Finance Health Check 50/30/20",
    page_icon="💰",
    layout="wide",  # Wide layout for better space utilization
    initial_sidebar_state="expanded"  # Show sidebar by default
)

# ============================================================================
# IMPORTS (AFTER set_page_config)
# ============================================================================
import asyncio
import pandas as pd
from io import BytesIO
import os
import re
import tempfile
import logging
from dotenv import load_dotenv

# Import core business logic modules
from finance_app.logic import load_currencies, is_valid_income, get_currency_symbol, validate_file, analyze_data, calculate_health_score
from finance_app.ai import get_ai_insights
from finance_app.pdf_generator import generate_pdf
from finance_app.config import get_pdf_filename, get_template_filename, DOWNLOADS_PATH
from finance_app.logging_config import setup_logging, get_logger

# Load environment variables (e.g., GEMINI_API_KEY) from .env file
load_dotenv()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Initialize logging with INFO level for file, WARNING for console
# This prevents excessive logging to console while keeping detailed file logs
logger = setup_logging(
    log_level=logging.INFO,        # Log INFO+ to app.log
    log_file='app.log',             # Log file path
    console_level=logging.WARNING,  # Only WARNING+ to console/terminal
    max_bytes=10*1024*1024,         # 10MB per log file
    backup_count=5                  # Keep 5 backup log files
)

# ============================================================================
# CONSTANTS
# ============================================================================
MAX_FILE_SIZE_MB = 5  # Maximum allowed Excel file size in megabytes
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes for comparison

# ============================================================================
# CACHED FUNCTIONS FOR PERFORMANCE OPTIMIZATION
# ============================================================================
# These functions use Streamlit's caching to avoid expensive operations
# on every app rerun, significantly improving responsiveness.

@st.cache_data
def get_currencies_data():
    """Cached wrapper for loading currencies.
    
    Caches the currency list from JSON file so it's only loaded once per session.
    This avoids repeated file I/O operations.
    
    Returns:
        list: List of currency dictionaries with 'code' and 'symbol' keys
    """
    return load_currencies()

@st.cache_data
def parse_and_validate_file(file_bytes):
    """Parse and validate Excel file with caching.
    
    Consolidates file reading into a single operation that handles both:
    1. Validation: Checks data integrity and format compliance
    2. Preview: Prepares DataFrame for display in the UI
    
    This eliminates redundant file I/O (was 3 reads, now 1 read).
    
    Args:
        file_bytes (bytes): Raw file contents from uploaded Excel file
        
    Returns:
        tuple: (is_valid: bool, validation_result: list, preview_df: DataFrame)
            - is_valid: Whether file passed all validation checks
            - validation_result: List of (row_num, error_msg) tuples if invalid
            - preview_df: DataFrame for UI preview (first 50 rows)
    """
    # Single validation operation that returns structured errors
    is_valid, validation_result = validate_file(BytesIO(file_bytes))
    
    # Create preview DataFrame for UI display
    try:
        preview_df = pd.read_excel(BytesIO(file_bytes))
        # Ensure Amount column is numeric for proper formatting
        if 'Amount' in preview_df.columns:
            preview_df['Amount'] = pd.to_numeric(preview_df['Amount'], errors='coerce')
    except (ValueError, KeyError, IOError) as e:
        logger.error(f"Failed to read Excel preview: {type(e).__name__}")
        preview_df = None
    except Exception as e:
        logger.error(f"Unexpected error reading Excel: {type(e).__name__}")
        preview_df = None
    
    return is_valid, validation_result, preview_df

# Load currencies from JSON file (cached on first load)
currencies = get_currencies_data()
# Extract currency codes and symbols into lookup dictionaries for UI binding
currency_codes = [c['code'] for c in currencies]
currency_symbols = {c['code']: c['symbol'] for c in currencies}

# ============================================================================
# CUSTOM CSS FOR STYLING
# ============================================================================
# Custom CSS for interactive tooltips that explain 50/30/20 rule
st.markdown("""
    <style>
    .main {
        max-width: 1000px;
    }
    /* Tooltip styles */
    .tooltip { position: relative; display: inline-block; }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 320px;
        background-color: #222;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 0;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        font-size: 0.9rem;
        line-height: 1.3;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 12px;
        border-width: 6px;
        border-style: solid;
        border-color: #222 transparent transparent transparent;
    }
    .tooltip-label { text-decoration: underline dotted; cursor: help; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Finance Health Check 50/30/20")
st.markdown(
    "<span class='tooltip'>"
    "<span class='tooltip-label'>Analyze your financial health with the 50/30/20 budgeting rule</span>"
    "<span class='tooltiptext'>50/30/20 = 50% needs (essentials), 30% wants (flexible), 20% savings (future).</span>"
    "</span>",
    unsafe_allow_html=True
)


# Initialize session state
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "currency" not in st.session_state:
    st.session_state.currency = "GBP"

# Sidebar for income input
with st.sidebar:
    st.header("📊 Setup")
    
    # Income input
    income = st.number_input(
        "Monthly Income",
        min_value=0.0,
        value=2000.0,
        step=100.0,
        help="Enter your monthly income"
    )
    
    # Currency selection from currencies.json
    currency = st.selectbox(
        "Currency",
        currency_codes,
        index=currency_codes.index("GBP") if "GBP" in currency_codes else 0,
        help="Select your currency",
        format_func=lambda code: f"{code} - {currency_symbols.get(code, '')}"
    )
    
    st.session_state.currency = currency
    
    # Get currency symbol for display
    currency_symbol = get_currency_symbol(currencies, currency)
    
    # Direct template download
    try:
        template_path = "data/Finance Health Check 50_30_20 Templates.xlsx"
        with open(template_path, "rb") as f:
            template_data = f.read()
        st.download_button(
            label="📥 Download Excel Template",
            data=template_data,
            file_name=get_template_filename(),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except FileNotFoundError:
        st.error("❌ Template file not found")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload Your Financial Data")
    
    # Validate income first
    if not is_valid_income(income):
        st.error(f"❌ Invalid income. Please enter a valid amount (minimum: {currency_symbol}100)")
    else:
        st.success(f"✅ Income valid: {currency_symbol}{income:,.2f}")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your Excel file",
            type=["xlsx"],
            help="Upload the Excel file with your expenses"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            
            # Get file bytes
            file_bytes = uploaded_file.getvalue()
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            # Validate file size
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                st.error(f"❌ File too large! Maximum size is {MAX_FILE_SIZE_MB}MB. Your file is {file_size_mb:.2f}MB.")
            else:
                # Use cached parsing and validation function
                is_valid, validation_result, df_preview = parse_and_validate_file(file_bytes)
                
                # Initialize error_rows set (will be populated if validation fails)
                error_rows = set()
                
                # Display validation results
                if not is_valid and validation_result:
                    # Extract row numbers and messages from structured errors
                    error_rows = {row_num for row_num, _ in validation_result}
                    error_messages = [f"Row {row_num}: {msg}" if row_num > 0 else msg 
                                    for row_num, msg in validation_result]
                    st.error(f"❌ Validation Error: {', '.join(error_messages)}")
                elif is_valid:
                    st.success("✅ File validated successfully!")
                
                # Show preview if available
                if df_preview is not None:
                    st.subheader("👀 Preview (first 50 rows)")
                    if error_rows:
                        st.info("Rows highlighted in red have validation issues.")
                        def highlight_row(row):
                            return ['background-color: #ffe6e6' if (row.name + 1) in error_rows else '' for _ in row]
                        # Format Amount to 3 decimal places in preview
                        styled = (
                            df_preview.head(50)
                            .style
                            .apply(highlight_row, axis=1)
                            .format({'Amount': lambda x: f"{x:.2f}" if pd.notnull(x) else ''})
                        )
                        st.dataframe(styled, use_container_width=True, height=400)
                    else:
                        # Format Amount to 3 decimal places in preview
                        styled = (
                            df_preview.head(50)
                            .style
                            .format({'Amount': lambda x: f"{x:.2f}" if pd.notnull(x) else ''})
                        )
                        st.dataframe(styled, use_container_width=True, height=400)
                
                # Validate and analyze
                if st.button("🔍 Analyze", use_container_width=True, disabled=not is_valid):
                    with st.spinner("Validating file and analyzing data..."):
                        try:
                            if not is_valid:
                                st.error("❌ Please fix validation errors before analysis.")
                            else:
                                # validation_result is validated DataFrame
                                needs, wants, savings, top_wants = analyze_data(validation_result, income)
                                
                                # Calculate health score
                                health_score = calculate_health_score(income, needs, wants, savings)
                                
                                # Generate AI insights with currency context (async call wrapped with asyncio.run)
                                score, advice = asyncio.run(get_ai_insights(income, needs, wants, savings, top_wants.to_dict(), currency))
                                
                                st.session_state.analysis_done = True
                                st.session_state.analysis_result = {
                                    'needs': needs,
                                    'wants': wants,
                                    'savings': savings,
                                    'top_wants': top_wants
                                }
                                st.session_state.health_score = health_score
                                st.session_state.advice = advice
                                st.rerun()
                        except (ValueError, IOError) as e:
                            logger.error(f"Analysis failed: {type(e).__name__}")
                            st.error(f"❌ Error processing file: {type(e).__name__}")
                        except Exception as e:
                            logger.error(f"Unexpected error during analysis: {type(e).__name__}")
                            st.error("❌ Unexpected error during analysis. Please try again.")

with col2:
    st.subheader("📋 Income Summary")
    st.metric("Monthly Income", f"{currency_symbol}{income:,.2f}")

# Display results if analysis is done
if st.session_state.analysis_done and "analysis_result" in st.session_state:
    result = st.session_state.analysis_result
    
    st.divider()
    st.subheader("📊 Analysis Results")
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Needs (50%)",
            f"{currency_symbol}{result['needs']:,.2f}",
            f"📊 {(result['needs']/income)*100:.1f}%"
        )
    
    with col2:
        st.metric(
            "Wants (30%)",
            f"{currency_symbol}{result['wants']:,.2f}",
            f"📊 {(result['wants']/income)*100:.1f}%"
        )
    
    with col3:
        st.metric(
            "Savings (20%)",
            f"{currency_symbol}{result['savings']:,.2f}",
            f"📊 {(result['savings']/income)*100:.1f}%"
        )
    
    # Health Score
    health_score = st.session_state.health_score
    advice = st.session_state.advice
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Financial Health Score")
        
        # Color coding based on score
        if health_score >= 80:
            color = "🟢"
        elif health_score >= 60:
            color = "🟡"
        else:
            color = "🔴"
        
        st.metric("Health Score", f"{color} {health_score:.1f}/100")
        
        # Score interpretation
        if health_score >= 80:
            interpretation = "Excellent - Your finances are well-balanced!"
        elif health_score >= 60:
            interpretation = "Good - Room for improvement in budget allocation"
        else:
            interpretation = "Needs Attention - Consider rebalancing your budget"
        
        st.info(interpretation)
    
    with col2:
        st.subheader("💡 AI Advice")
        st.success("✅ Advice generated!")
        st.markdown(advice)
    
    # Display charts if available
    if "chart_image" in result:
        st.divider()
        st.subheader("📈 Visual Analysis")
        st.image(result["chart_image"], use_container_width=True)
    
    # Download PDF report
    st.divider()
    st.subheader("📥 Download Report")
    
    if st.button("📄 Generate PDF Report", use_container_width=True):
        with st.spinner("Generating PDF report..."):
            try:
                # Create temporary file for PDF
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    pdf_path = tmp_file.name
                
                # Call generate_pdf with correct signature
                generate_pdf(
                    path=pdf_path,
                    income=income,
                    symbol=currency_symbol,
                    needs=result['needs'],
                    wants=result['wants'],
                    savings=result['savings'],
                    top_wants=result['top_wants'],
                    score=health_score,
                    advice=advice
                )
                
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=get_pdf_filename(),
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generated successfully!")
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
    
    # Reset button
    if st.button("🔄 Start New Analysis", use_container_width=True):
        st.session_state.analysis_done = False
        st.session_state.uploaded_file = None
        st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; margin-top: 20px;'>
    <p>Finance Health Check 50/30/20 | Built with Streamlit</p>
        <p>
            <span class="tooltip">
                <span class="tooltip-label">Analyze your spending using the proven 50/30/20 budgeting method</span>
                <span class="tooltiptext">50/30/20 = 50% needs (essentials), 30% wants (flexible), 20% savings (future).</span>
            </span>
        </p>
        <p style='margin-top: 8px;'>
          <a href="https://github.com/adityanandaaa/PSFE-Individual-Assignment" target="_blank" rel="noopener" style="color:#3b82f6; text-decoration: none;">🔗 View Source on GitHub</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
