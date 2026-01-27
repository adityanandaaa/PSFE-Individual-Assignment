import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

def generate_bar_chart(needs, wants, savings, income, symbol):
    """Generate bar chart comparing actual spending vs 50/30/20 targets.
    
    Creates a matplotlib bar chart with overlaid target line for visual budget
    analysis. Chart is saved as temporary PNG file.
    
    Args:
        needs, wants, savings: Actual spending amounts for each category
        income: Monthly income (used to calculate targets)
        symbol: Currency symbol for y-axis label
        
    Returns:
        str: Path to temporary PNG file
    """
    # Define budget categories
    categories = ['Needs', 'Wants', 'Savings']
    # Actual spending amounts
    values = [needs, wants, savings]
    # Calculate 50/30/20 targets
    targets = [income * 0.5, income * 0.3, income * 0.2]
    
    # Create figure and bar plot
    plt.figure(figsize=(6, 4))
    plt.bar(categories, values, color=['blue', 'red', 'green'], label='Actual')
    # Overlay target line for easy comparison
    plt.plot(categories, targets, 'o-', color='black', label='Targets')
    plt.title('Spending vs Targets')
    plt.ylabel(f'Amount ({symbol})')
    plt.legend()
    # Format y-axis ticks to two decimals
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    
    # Save to temporary file and close plot
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_pie_chart(needs, wants, savings):
    """Generate pie chart showing expense breakdown percentages.
    
    Creates a matplotlib pie chart with percentage labels for visual
    representation of budget allocation.
    
    Args:
        needs, wants, savings: Spending amounts for each category
        
    Returns:
        str: Path to temporary PNG file
    """
    # Define pie slices and colors
    labels = ['Needs', 'Wants', 'Savings']
    sizes = [needs, wants, savings]
    colors = ['blue', 'red', 'green']
    
    # Create pie chart with percentage labels
    plt.figure(figsize=(6, 6))
    # Show percentages with two decimals
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.2f%%', startangle=140)
    plt.title('Expense Breakdown')
    plt.axis('equal')  # Ensure pie is circular
    
    # Save to temporary file and close plot
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_category_chart(top_wants, symbol):
    """Generate bar chart for top 5 spending categories in Wants.
    
    Shows the breakdown of wants spending by category to help identify
    areas for potential cost reduction.
    
    Args:
        top_wants: Pandas Series with category names and amounts
        symbol: Currency symbol for y-axis label
        
    Returns:
        str: Path to temporary PNG file
    """
    # Extract category names and amounts from Series
    categories = list(top_wants.keys())
    amounts = list(top_wants.values)
    
    # Create horizontal bar chart for better category label readability
    plt.figure(figsize=(8, 6))
    plt.bar(categories, amounts, color='orange')
    plt.title('Top Wants Categories')
    plt.ylabel(f'Amount ({symbol})')
    plt.xticks(rotation=45)  # Rotate labels for better readability
    plt.tight_layout()
    # Format y-axis ticks to two decimals
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    
    # Save to temporary file and close plot
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_pdf(path, income, symbol, needs, wants, savings, top_wants, score, advice):
    """Generate comprehensive financial health report PDF.
    
    Creates a professional PDF report with budget summary, AI health score,
    personalized advice, and visual charts for analysis.
    
    Args:
        path: Output PDF file path
        income: Monthly income
        symbol: Currency symbol
        needs, wants, savings: Budget category amounts
        top_wants: Pandas Series of top 5 want categories
        score: AI health score (0-100)
        advice: AI-generated financial advice
    """
    # Initialize PDF document with letter size
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # === HEADER ===
    story.append(Paragraph(f"Financial Health Report - Income: {symbol}{income:,.2f}", styles['Heading1']))
    story.append(Spacer(1, 12))
    
    # === BUDGET SUMMARY ===
    # Display actual spending vs 50/30/20 targets
    story.append(Paragraph(f"Needs: {symbol}{needs:,.2f} (50% target: {symbol}{income*0.5:,.2f})", styles['Normal']))
    story.append(Paragraph(f"Wants: {symbol}{wants:,.2f} (30% target: {symbol}{income*0.3:,.2f})", styles['Normal']))
    story.append(Paragraph(f"Savings: {symbol}{savings:,.2f} (20% target: {symbol}{income*0.2:,.2f})", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # === AI INSIGHTS ===
    # Display health score and recommendations
    story.append(Paragraph(f"Health Score: {score}", styles['Normal']))
    story.append(Paragraph(f"Advice: {advice}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # === GENERATE CHARTS ===
    # Create all three visualization charts
    bar_path = generate_bar_chart(needs, wants, savings, income, symbol)
    pie_path = generate_pie_chart(needs, wants, savings)
    category_path = generate_category_chart(top_wants, symbol)
    
    # === BAR CHART SECTION ===
    story.append(Paragraph("Spending vs Targets", styles['Heading2']))
    story.append(Image(bar_path, width=400, height=500))
    story.append(Paragraph("This bar chart compares your actual spending in Needs, Wants, and Savings against the 50/30/20 targets.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # === PIE CHART SECTION ===
    story.append(Paragraph("Expense Breakdown", styles['Heading2']))
    story.append(Image(pie_path, width=400, height=500))
    story.append(Paragraph("This pie chart shows the percentage breakdown of your expenses across Needs, Wants, and Savings.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # === CATEGORY CHART SECTION ===
    story.append(Paragraph("Top Wants Categories", styles['Heading2']))
    story.append(Image(category_path, width=400, height=500))
    story.append(Paragraph("This bar chart displays the top 5 spending categories in Wants.", styles['Normal']))
    
    # === BUILD PDF ===
    doc.build(story)
    
    # === CLEANUP TEMPORARY FILES ===
    # Remove temporary chart PNG files after PDF is generated
    os.unlink(bar_path)
    os.unlink(pie_path)
    os.unlink(category_path)