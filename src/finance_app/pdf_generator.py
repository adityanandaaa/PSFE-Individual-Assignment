import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
    
    # Create figure and bar plot with enhanced styling
    plt.figure(figsize=(8, 5))
    bar_colors = ['#4A90E2', '#E74C3C', '#2ECC71']
    bars = plt.bar(categories, values, color=bar_colors, label='Actual', alpha=0.8, edgecolor='black', linewidth=1.2)
    
    # Overlay target line for easy comparison
    plt.plot(categories, targets, 'o-', color='#34495E', linewidth=2.5, markersize=8, label='Target (50/30/20)')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{symbol}{height:,.0f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.title('Spending vs Targets', fontsize=14, fontweight='bold', pad=15)
    plt.ylabel(f'Amount ({symbol})', fontsize=11)
    plt.xlabel('Category', fontsize=11)
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    # Format y-axis ticks to two decimals
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    plt.tight_layout()
    
    # Save to temporary file and close plot
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_pie_chart(needs, wants, savings, income):
    """Generate pie chart showing expense breakdown percentages.
    
    Creates a matplotlib pie chart with percentage labels for visual
    representation of budget allocation relative to income.
    
    Args:
        needs, wants, savings: Spending amounts for each category
        income: Monthly income (used to calculate percentages)
        
    Returns:
        str: Path to temporary PNG file
    """
    # Define pie slices and colors
    labels = ['Needs', 'Wants', 'Savings']
    sizes = [needs, wants, savings]
    pie_colors = ['#4A90E2', '#E74C3C', '#2ECC71']
    explode = (0.05, 0.05, 0.05)  # Slightly separate slices
    
    # Create pie chart with percentage labels
    plt.figure(figsize=(7, 7))
    
    # Custom autopct function to show only amount (not percentage)
    def make_autopct(values):
        def my_autopct(pct):
            # Find which slice this percentage corresponds to
            total = sum(values)
            # Calculate actual value from the pie percentage
            val = pct * total / 100
            # Find closest match to determine which category
            diffs = [abs(val - v) for v in values]
            idx = diffs.index(min(diffs))
            return f'{values[idx]:,.0f}'
        return my_autopct
    
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=pie_colors, 
                                        autopct=make_autopct(sizes),
                                        startangle=140,
                                        explode=explode, shadow=True,
                                        textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    # Style amount text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
    
    plt.title('Expense Breakdown', fontsize=14, fontweight='bold', pad=20)
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
    # Use a vibrant color palette for visual variety
    colors_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    bar_colors = colors_palette[:len(categories)]
    
    plt.figure(figsize=(8, 6))
    plt.bar(categories, amounts, color=bar_colors)
    plt.title('Top Wants Categories')
    plt.ylabel(f'Amount ({symbol})')
    plt.xticks(rotation=45, ha='right')  # Rotate labels and align right for better readability
    # Format y-axis ticks to two decimals
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    plt.tight_layout(pad=2.0)  # Add padding to prevent cutoff
    
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
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=36, bottomMargin=36, leftMargin=42, rightMargin=42)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles['Heading2'], textColor=colors.HexColor('#0B6EEF')))
    styles.add(ParagraphStyle(name="Kpi", parent=styles['Heading1'], textColor=colors.HexColor('#0B6EEF'), spaceAfter=6))
    styles.add(ParagraphStyle(name="Muted", parent=styles['Normal'], textColor=colors.HexColor('#4D4D4D'), leading=14))
    story = []
    
    # === HEADER ===
    story.append(Paragraph(f"Financial Health Report", styles['Heading1']))
    story.append(Paragraph(f"Monthly income: {symbol}{income:,.2f}", styles['Muted']))
    story.append(Spacer(1, 10))

    # === KPI STRIP ===
    score_label = "Health Score"
    kpi_table = Table(
        [[Paragraph(f"<b>{score_label}</b>", styles['Normal']), Paragraph(f"<b>{score}/100</b>", styles['Kpi'])]],
        colWidths=[2.5*inch, 1.5*inch]
    )
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F1FF')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#0B3B8C')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#0B3B8C')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C7D7F4')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#C7D7F4')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))
    
    # === BUDGET BREAKDOWN TABLE ===
    # Professional table showing actual vs target spending
    needs_pct = (needs / income * 100) if income else 0
    wants_pct = (wants / income * 100) if income else 0
    savings_pct = (savings / income * 100) if income else 0
    
    budget_data = [
        [Paragraph("<b>Category</b>", styles['Normal']), 
         Paragraph("<b>Actual</b>", styles['Normal']), 
         Paragraph("<b>Target</b>", styles['Normal'])],
        [Paragraph("Needs", styles['Normal']), 
         Paragraph(f"{symbol}{needs:,.2f}<br/><font size=9 color='#666666'>({needs_pct:.1f}%)</font>", styles['Normal']), 
         Paragraph(f"{symbol}{income*0.5:,.2f}<br/><font size=9 color='#666666'>(50.0%)</font>", styles['Normal'])],
        [Paragraph("Wants", styles['Normal']), 
         Paragraph(f"{symbol}{wants:,.2f}<br/><font size=9 color='#666666'>({wants_pct:.1f}%)</font>", styles['Normal']), 
         Paragraph(f"{symbol}{income*0.3:,.2f}<br/><font size=9 color='#666666'>(30.0%)</font>", styles['Normal'])],
        [Paragraph("Savings", styles['Normal']), 
         Paragraph(f"{symbol}{savings:,.2f}<br/><font size=9 color='#666666'>({savings_pct:.1f}%)</font>", styles['Normal']), 
         Paragraph(f"{symbol}{income*0.2:,.2f}<br/><font size=9 color='#666666'>(20.0%)</font>", styles['Normal'])]
    ]
    
    budget_table = Table(budget_data, colWidths=[1.5*inch, 2.25*inch, 2.25*inch])
    budget_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B6EEF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FA')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D9E0')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#0B6EEF')),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10)
    ]))
    
    story.append(budget_table)
    story.append(Spacer(1, 18))
    
    # === AI INSIGHTS ===
    # Display health score and recommendations
    # === AI INSIGHTS ===
    story.append(Paragraph("AI Guidance", styles['SectionHeading']))
    story.append(Paragraph(advice.replace("\n", "<br/>"), styles['Normal']))
    story.append(Spacer(1, 14))
    
    # === GENERATE CHARTS ===
    # Create all three visualization charts
    bar_path = generate_bar_chart(needs, wants, savings, income, symbol)
    pie_path = generate_pie_chart(needs, wants, savings, income)
    category_path = generate_category_chart(top_wants, symbol)

    # Precompute insights for chart captions
    # Describe dominant shares
    mix = {"Needs": needs_pct, "Wants": wants_pct, "Savings": savings_pct}
    largest_label = max(mix, key=mix.get)
    largest_value = mix[largest_label]
    # Top wants categories text
    top_wants_items = list(top_wants.items()) if hasattr(top_wants, 'items') else []
    top_wants_desc = ", ".join([f"{k}: {v:,.2f}{symbol}" for k, v in top_wants_items[:3]]) if top_wants_items else "No top wants categories provided"
    
    # === BAR CHART SECTION ===
    story.append(Paragraph("Spending vs Targets", styles['SectionHeading']))
    story.append(Image(bar_path, width=5.5*inch, height=3.6*inch))
    story.append(Paragraph(
        f"Actual mix: Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%. Aim for 50/30/20.",
        styles['Muted']
    ))
    story.append(Paragraph("Tip: bring Wants closer to 30% and direct the difference into Savings.", styles['Muted']))
    story.append(Spacer(1, 12))
    
    # === PIE CHART SECTION ===
    story.append(Paragraph("Expense Breakdown", styles['SectionHeading']))
    story.append(Image(pie_path, width=5.5*inch, height=3.6*inch))
    story.append(Paragraph(
        f"Your spending distribution: Needs {needs_pct:.1f}%, Wants {wants_pct:.1f}%, Savings {savings_pct:.1f}%. "
        f"The largest category is {largest_label} at {largest_value:.1f}%.",
        styles['Muted']
    ))
    story.append(Paragraph("The 50/30/20 rule suggests 50% for Needs, 30% for Wants, and 20% for Savings. Focus on rebalancing over-allocated categories.", styles['Muted']))
    story.append(Spacer(1, 12))
    
    # === CATEGORY CHART SECTION ===
    story.append(Paragraph("Top Wants Categories", styles['SectionHeading']))
    story.append(Image(category_path, width=5.5*inch, height=3.6*inch))
    story.append(Paragraph(f"Biggest discretionary areas: {top_wants_desc}.", styles['Muted']))
    story.append(Paragraph("Trim 1–2 of these categories and redirect that amount to savings.", styles['Muted']))
    
    # === BUILD PDF ===
    doc.build(story)
    
    # === CLEANUP TEMPORARY FILES ===
    # Remove temporary chart PNG files after PDF is generated
    os.unlink(bar_path)
    os.unlink(pie_path)
    os.unlink(category_path)