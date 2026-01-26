import streamlit as st
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv

from modules.logic import is_valid_income, validate_file, analyze_data, calculate_health_score
from modules.ai import generate_advice
from modules.pdf_generator import generate_pdf
from modules.config import get_pdf_filename, get_template_filename, DOWNLOADS_PATH

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Finance Check 50/30/20",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        max-width: 1000px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Finance Check 50/30/20")
st.markdown("Analyze your financial health with the 50/30/20 budgeting rule")

# Initialize session state
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "currency" not in st.session_state:
    st.session_state.currency = "USD"

# Sidebar for income input
with st.sidebar:
    st.header("📊 Setup")
    
    # Income input
    income = st.number_input(
        "Monthly Income",
        min_value=0.0,
        value=5000.0,
        step=100.0,
        help="Enter your monthly income"
    )
    
    # Currency selection
    currency = st.selectbox(
        "Currency",
        ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "INR", "SGD"],
        index=0,
        help="Select your currency"
    )
    
    st.session_state.currency = currency
    
    # Download template button
    if st.button("📥 Download Template", use_container_width=True):
        try:
            template_path = f"Finance Check 50_30_20 Templates.xlsx"
            with open(template_path, "rb") as f:
                template_data = f.read()
            
            st.download_button(
                label="📥 Download Excel Template",
                data=template_data,
                file_name=get_template_filename(),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("✅ Template ready for download!")
        except FileNotFoundError:
            st.error("❌ Template file not found")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload Your Financial Data")
    
    # Validate income first
    if not is_valid_income(income):
        st.error(f"❌ Invalid income. Please enter a valid amount (minimum: {currency} 100)")
    else:
        st.success(f"✅ Income valid: {currency} {income:,.2f}")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your Excel file",
            type=["xlsx"],
            help="Upload the Excel file with your expenses"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            
            # Validate and analyze
            if st.button("🔍 Analyze", use_container_width=True):
                with st.spinner("Validating file and analyzing data..."):
                    try:
                        # Validate file
                        is_valid, message = validate_file(uploaded_file)
                        
                        if not is_valid:
                            st.error(f"❌ Validation Error: {message}")
                        else:
                            st.success(f"✅ {message}")
                            
                            # Analyze data
                            result = analyze_data(uploaded_file, income, currency)
                            
                            if result["success"]:
                                st.session_state.analysis_done = True
                                st.session_state.analysis_result = result
                                st.rerun()
                            else:
                                st.error(f"❌ Analysis Error: {result['message']}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

with col2:
    st.subheader("📋 Income Summary")
    st.metric("Monthly Income", f"{currency} {income:,.2f}")

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
            f"{currency} {result['needs']:,.2f}",
            f"{(result['needs']/income)*100:.1f}% of income"
        )
    
    with col2:
        st.metric(
            "Wants (30%)",
            f"{currency} {result['wants']:,.2f}",
            f"{(result['wants']/income)*100:.1f}% of income"
        )
    
    with col3:
        st.metric(
            "Savings (20%)",
            f"{currency} {result['savings']:,.2f}",
            f"{(result['savings']/income)*100:.1f}% of income"
        )
    
    # Health Score
    health_score = calculate_health_score(income, result['needs'], result['wants'], result['savings'])
    
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
        with st.spinner("Generating personalized advice..."):
            advice_response = generate_advice(income, result['needs'], result['wants'], result['savings'])
            
            if advice_response["success"]:
                st.success("✅ Advice generated!")
                st.markdown(advice_response["advice"])
            else:
                st.warning("⚠️ Could not generate AI advice (API unavailable)")
                st.info("Basic Advice: Focus on the 50/30/20 rule and adjust spending in areas where you exceed the targets.")
    
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
                pdf_path = generate_pdf(income, currency, result, health_score, advice_response.get("advice", ""))
                
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
    <p>Finance Check 50/30/20 | Built with Streamlit</p>
    <p>Analyze your spending using the proven 50/30/20 budgeting method</p>
    </div>
    """, unsafe_allow_html=True)
