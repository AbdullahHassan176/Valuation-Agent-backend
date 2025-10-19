#!/usr/bin/env python3
"""
Create a simple test PDF for contract parsing testing.
"""

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
except ImportError:
    print("reportlab not installed. Install with: pip install reportlab")
    exit(1)

def create_test_pdf():
    """Create a test PDF with contract text."""
    
    filename = "test_contract.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Contract content
    content = [
        Paragraph("INTEREST RATE SWAP AGREEMENT", title_style),
        Spacer(1, 20),
        
        Paragraph("This Interest Rate Swap Agreement (the \"Agreement\") is entered into on January 15, 2024, between:", normal_style),
        Paragraph("Counterparty A: ABC Bank", normal_style),
        Paragraph("Counterparty B: XYZ Corporation", normal_style),
        Spacer(1, 20),
        
        Paragraph("TERMS AND CONDITIONS:", heading_style),
        
        Paragraph("1. NOTIONAL AMOUNT: USD 10,000,000 (Ten Million US Dollars)", normal_style),
        Paragraph("2. CURRENCY: USD (United States Dollar)", normal_style),
        Paragraph("3. FIXED RATE: 5.25% per annum", normal_style),
        Paragraph("4. FLOATING RATE INDEX: SOFR (Secured Overnight Financing Rate)", normal_style),
        Paragraph("5. EFFECTIVE DATE: March 1, 2024", normal_style),
        Paragraph("6. MATURITY DATE: March 1, 2025", normal_style),
        Paragraph("7. PAYMENT FREQUENCY: Quarterly", normal_style),
        Paragraph("8. DAY COUNT CONVENTION: ACT/360", normal_style),
        Paragraph("9. BUSINESS DAY CONVENTION: Following", normal_style),
        Paragraph("10. CALENDAR: USD Calendar", normal_style),
        Spacer(1, 20),
        
        Paragraph("This swap agreement represents a standard interest rate swap where Counterparty A will pay a fixed rate of 5.25% and receive SOFR floating rate payments on a notional amount of USD 10,000,000.", normal_style),
        Spacer(1, 10),
        
        Paragraph("The swap will commence on March 1, 2024 and terminate on March 1, 2025, with quarterly payment dates.", normal_style),
        Spacer(1, 10),
        
        Paragraph("All payments will be calculated using the ACT/360 day count convention and the Following business day convention will apply to all payment dates.", normal_style),
        Spacer(1, 10),
        
        Paragraph("This agreement is subject to standard ISDA terms and conditions.", normal_style),
    ]
    
    doc.build(content)
    print(f"Test PDF created: {filename}")
    return filename

if __name__ == "__main__":
    create_test_pdf()



