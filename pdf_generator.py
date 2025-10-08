"""PDF Report Generator for TieShop Bot - Modern Design"""


import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Rect, Circle
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# Register custom fonts
def register_fonts():
    """Register custom fonts for better rendering"""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(script_dir, 'fonts')
        
        # Register Helvetica fonts
        helvetica_path = os.path.join(fonts_dir, 'Helvetica.ttf')
        helvetica_bold_path = os.path.join(fonts_dir, 'Helvetica-Bold.ttf')
        helvetica_light_path = os.path.join(fonts_dir, 'helvetica-light-587ebe5a59211.ttf')
        
        if os.path.exists(helvetica_path):
            pdfmetrics.registerFont(TTFont('Helvetica-Regular', helvetica_path))
        if os.path.exists(helvetica_bold_path):
            pdfmetrics.registerFont(TTFont('Helvetica-Bold', helvetica_bold_path))
        if os.path.exists(helvetica_light_path):
            pdfmetrics.registerFont(TTFont('Helvetica-Light', helvetica_light_path))
            
    except Exception as e:
        print(f"Warning: Could not register custom fonts: {e}")

# Register fonts when module is imported
register_fonts()

def generate_admin_report(orders, users, output_path='admin_report.pdf'):
    """Generate modern admin report with beautiful design"""
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Modern color palette
    primary_color = colors.HexColor('#667eea')  # Modern blue
    secondary_color = colors.HexColor('#764ba2')  # Purple
    accent_color = colors.HexColor('#f093fb')  # Pink
    success_color = colors.HexColor('#4facfe')  # Light blue
    warning_color = colors.HexColor('#f093fb')  # Pink
    danger_color = colors.HexColor('#ff6b6b')  # Red
    dark_gray = colors.HexColor('#2d3748')
    light_gray = colors.HexColor('#f7fafc')
    
    # Modern styles with custom fonts
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=primary_color,
        spaceAfter=20,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=dark_gray,
        spaceAfter=15,
        spaceBefore=25,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontSize=16,
        textColor=secondary_color,
        spaceAfter=10,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    info_style = ParagraphStyle(
        'InfoText',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=6,
        fontName='Helvetica-Regular'
    )
    
    # Simple header
    story.append(Paragraph("TieShop Business Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", info_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Key Metrics Cards
    story.append(Paragraph("Key Performance Indicators", subtitle_style))
    
    # Calculate metrics
    total_orders = len(orders)
    total_users = len(users)
    completed_orders = sum(1 for o in orders if o.status == 'completed')
    pending_orders = sum(1 for o in orders if o.status in ['pending_payment', 'pending_admin_review'])
    total_revenue = sum(o.price for o in orders if o.status == 'completed')
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # Simple metrics table
    metrics_data = [
        ['Metric', 'Value'],
        ['Total Orders', f'{total_orders:,}'],
        ['Total Users', f'{total_users:,}'],
        ['Completed Orders', f'{completed_orders:,}'],
        ['Pending Orders', f'{pending_orders:,}'],
        ['Total Revenue', f'{total_revenue:,.0f} тг'],
        ['Average Order Value', f'{avg_order_value:,.0f} тг'],
        ['Success Rate', f'{(completed_orders/total_orders*100):.1f}%' if total_orders > 0 else '0%']
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Regular'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(metrics_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Add page break before orders section
    story.append(PageBreak())
    
    # Order Management Section
    story.append(Paragraph("Order Management", subtitle_style))
    
    # Simple order status summary
    status_summary = {}
    for order in orders:
        status = order.status
        if status not in status_summary:
            status_summary[status] = {'count': 0, 'revenue': 0}
        status_summary[status]['count'] += 1
        if order.status == 'completed':
            status_summary[status]['revenue'] += order.price
    
    status_data = [['Status', 'Count', 'Revenue']]
    for status, data in status_summary.items():
        status_data.append([
            status.replace('_', ' ').title(),
            str(data['count']),
            f"{data['revenue']:,.0f} тг"
        ])
    
    status_table = Table(status_data, colWidths=[2*inch, 1*inch, 1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Regular'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(status_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Detailed orders with full customer info
    story.append(Paragraph("Detailed Orders Information", section_style))
    
    recent_orders = sorted(orders, key=lambda x: x.created_at, reverse=True)[:15]
    
    for i, order in enumerate(recent_orders):
        # Order header
        order_header = f"Order #{order.id} - {order.status.replace('_', ' ').title()}"
        story.append(Paragraph(order_header, section_style))
        
        # Customer and order details
        order_details = [
            ['Field', 'Information'],
            ['Order ID', f'#{order.id}'],
            ['Status', order.status.replace('_', ' ').title()],
            ['Date', order.created_at.strftime('%d.%m.%Y %H:%M')],
            ['', ''],
            ['Payer Information', ''],
            ['Name', order.recipient_name or 'N/A'],
            ['Surname', order.recipient_surname or 'N/A'],
            ['Phone', order.recipient_phone or 'N/A'],
            ['Address', order.delivery_address or 'N/A'],
            ['', ''],
            ['Product Information', ''],
            ['Product Name', order.tie_name or 'N/A'],
            ['Price', f'{order.price:,.0f} тг' if order.price else 'N/A'],
            ['', ''],
            ['Additional Info', ''],
            ['User ID', str(order.user_telegram_id)],
            ['Created', order.created_at.strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        order_table = Table(order_details, colWidths=[1.5*inch, 3.5*inch])
        order_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Regular'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            
            # Section headers
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 11),
            ('TEXTCOLOR', (0, 1), (0, -1), secondary_color),
            
            # Value styling
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Regular'),
            ('TEXTCOLOR', (1, 1), (1, -1), dark_gray),
            
            # Borders and spacing
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, primary_color),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(order_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Add page break every 3 orders
        if (i + 1) % 3 == 0 and i < len(recent_orders) - 1:
            story.append(PageBreak())
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"""
    <para align="center" fontSize="10" textColor="#718096">
    Generated by TieShop Analytics System | {datetime.now().strftime('%B %d, %Y at %H:%M')}
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return output_path

def generate_user_activity_report(user_sessions, output_path='user_activity.pdf'):
    """Generate modern user activity monitoring report"""
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Modern color palette
    primary_color = colors.HexColor('#667eea')
    secondary_color = colors.HexColor('#764ba2')
    success_color = colors.HexColor('#4facfe')
    light_gray = colors.HexColor('#f7fafc')
    dark_gray = colors.HexColor('#2d3748')
    
    # Modern styles
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=primary_color,
        spaceAfter=20,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=dark_gray,
        spaceAfter=15,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Header
    header_data = [
        ['User Activity Monitor', f'Real-time Report - {datetime.now().strftime("%B %d, %Y at %H:%M")}'],
        ['', 'Live Session Analytics Dashboard']
    ]
    
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), primary_color),
        ('BACKGROUND', (1, 0), (1, 0), secondary_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 20),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Activity summary
    active_sessions = [s for s in user_sessions if s.get('active')]
    total_sessions = len(user_sessions)
    
    # Summary cards
    summary_data = [
        [
            ['[GREEN]', 'Active Now', f'{len(active_sessions)}', 'Currently online'],
            ['[USERS]', 'Total Sessions', f'{total_sessions}', 'All time sessions'],
            ['[CLOCK]', 'Avg Duration', f'{sum((datetime.now() - s["start_time"]).total_seconds() / 60 for s in active_sessions) / len(active_sessions):.1f} min' if active_sessions else '0 min', 'Average session time'],
            ['[CHART]', 'Activity Rate', f'{(len(active_sessions)/total_sessions*100):.1f}%' if total_sessions > 0 else '0%', 'Active vs total sessions']
        ]
    ]
    
    for row in summary_data:
        summary_table = Table(row, colWidths=[0.5*inch, 1.2*inch, 1.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), light_gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), dark_gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('ALIGN', (3, 0), (3, 0), 'LEFT'),
            
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (2, 0), 14),
            ('TEXTCOLOR', (2, 0), (2, 0), primary_color),
            
            ('FONTSIZE', (3, 0), (3, 0), 8),
            ('TEXTCOLOR', (3, 0), (3, 0), colors.HexColor('#718096')),
            
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Active users table
    story.append(Paragraph("Currently Active Users", subtitle_style))
    
    active_data = [['User ID', 'Username', 'Current Action', 'Session Start', 'Duration']]
    for session in active_sessions:
            duration = (datetime.now() - session['start_time']).total_seconds() / 60
            active_data.append([
                str(session['user_id']),
            session.get('username', 'Anonymous'),
                session.get('current_action', 'Browsing'),
                session['start_time'].strftime('%H:%M'),
                f"{duration:.1f} min"
            ])
    
    if len(active_data) > 1:
        active_table = Table(active_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1*inch, 1*inch])
        active_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), success_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
            
            # Value styling
            ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (4, 1), (4, -1), primary_color),
            
            # Borders and spacing
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, success_color),
            ('PADDING', (0, 0), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_gray]),
        ]))
        story.append(active_table)
    else:
        no_users_text = """
        <para align="center" fontSize="14" textColor="#718096">
        No active users at the moment
        </para>
        """
        story.append(Paragraph(no_users_text, styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"""
    <para align="center" fontSize="10" textColor="#718096">
    Generated by TieShop Activity Monitor | {datetime.now().strftime('%B %d, %Y at %H:%M')}
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return output_path
