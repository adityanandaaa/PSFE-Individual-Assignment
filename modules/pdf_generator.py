import matplotlib.pyplot as plt
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

def generate_bar_chart(needs, wants, savings, income, symbol):
    """Generate bar chart for spending vs targets."""
    categories = ['Needs', 'Wants', 'Savings']
    values = [needs, wants, savings]
    targets = [income * 0.5, income * 0.3, income * 0.2]
    plt.figure(figsize=(6, 4))
    plt.bar(categories, values, color=['blue', 'red', 'green'], label='Actual')
    plt.plot(categories, targets, 'o-', color='black', label='Targets')
    plt.title('Spending vs Targets')
    plt.ylabel(f'Amount ({symbol})')
    plt.legend()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_pie_chart(needs, wants, savings):
    """Generate pie chart for expense breakdown."""
    labels = ['Needs', 'Wants', 'Savings']
    sizes = [needs, wants, savings]
    colors = ['blue', 'red', 'green']
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Expense Breakdown')
    plt.axis('equal')
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_category_chart(top_wants, symbol):
    """Generate bar chart for top wants categories."""
    categories = list(top_wants.keys())
    amounts = list(top_wants.values)
    plt.figure(figsize=(8, 6))
    plt.bar(categories, amounts, color='orange')
    plt.title('Top Wants Categories')
    plt.ylabel(f'Amount ({symbol})')
    plt.xticks(rotation=45)
    plt.tight_layout()
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp.name)
    plt.close()
    return tmp.name

def generate_pdf(path, income, symbol, needs, wants, savings, top_wants, score, advice):
    """Generate the PDF report."""
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Financial Health Report - Income: {symbol}{income}", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Needs: {symbol}{needs:.2f} (50% target: {symbol}{income*0.5:.2f})", styles['Normal']))
    story.append(Paragraph(f"Wants: {symbol}{wants:.2f} (30% target: {symbol}{income*0.3:.2f})", styles['Normal']))
    story.append(Paragraph(f"Savings: {symbol}{savings:.2f} (20% target: {symbol}{income*0.2:.2f})", styles['Normal']))
    story.append(Paragraph(f"Health Score: {score}", styles['Normal']))
    story.append(Paragraph(f"Advice: {advice}", styles['Normal']))
    story.append(Spacer(1, 12))
    # Generate charts
    bar_path = generate_bar_chart(needs, wants, savings, income, symbol)
    pie_path = generate_pie_chart(needs, wants, savings)
    category_path = generate_category_chart(top_wants, symbol)
    story.append(Paragraph("Spending vs Targets", styles['Heading2']))
    story.append(Image(bar_path, width=400, height=500))
    story.append(Paragraph("This bar chart compares your actual spending in Needs, Wants, and Savings against the 50/30/20 targets.", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Expense Breakdown", styles['Heading2']))
    story.append(Image(pie_path, width=400, height=500))
    story.append(Paragraph("This pie chart shows the percentage breakdown of your expenses across Needs, Wants, and Savings.", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Top Wants Categories", styles['Heading2']))
    story.append(Image(category_path, width=400, height=500))
    story.append(Paragraph("This bar chart displays the top 5 spending categories in Wants.", styles['Normal']))
    doc.build(story)
    # Clean up temp files
    os.unlink(bar_path)
    os.unlink(pie_path)
    os.unlink(category_path)