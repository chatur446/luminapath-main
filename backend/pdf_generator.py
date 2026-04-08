"""Creates professional PDF medical reports"""

import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors

from config import Config


def generate_medical_report(
    patient_name: str,
    patient_age: str,
    patient_id: str,
    oct_image_path: str,
    explanation_text: str,
    predicted_disease: str,
    gender: str,
    physician: str,
    email: str,
    language: str = "English",
    output_path: str = None
) -> str:
    """Builds the final medical PDF for the patient"""
    
    # Make sure we have all required info
    if not patient_name or not patient_name.strip():
        raise ValueError("patient_name is required and cannot be empty")
    if not patient_id or not patient_id.strip():
        raise ValueError("patient_id is required and cannot be empty")
    if not predicted_disease or not predicted_disease.strip():
        raise ValueError("predicted_disease is required and cannot be empty")
    if not email or not email.strip():
        raise ValueError("email is required and cannot be empty")
    if not gender or not gender.strip():
        raise ValueError("gender is required and cannot be empty")
    
    # Handle missing data gracefully
    age_str = str(patient_age) if patient_age else "Not Provided"
    physician_name = physician if physician and physician.strip() else "Not Specified"
    
    # Figure out where to save PDF
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Config.REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up patient ID for safe filename
        safe_patient_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in patient_id)
        output_path = str(reports_dir / f"Report_{safe_patient_id}_{timestamp}.pdf")
    
    # Set up PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40
    )
    
    # Content goes here
    story = []
    
    # Load default styles
    styles = getSampleStyleSheet()
    
    # Custom heading style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#424242'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Section header style
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    # Body text style
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    # Bullet style
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=6
    )
    
    # Top of document
    story.append(Paragraph("LuminaPath", title_style))
    story.append(Paragraph("AI-Powered Retinal Analysis Report", subtitle_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Report info
    report_date = datetime.now().strftime("%B %d, %Y")
    report_time = datetime.now().strftime("%I:%M %p")
    report_id = f"LP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    metadata = [
        ['Report Date:', report_date, 'Report Time:', report_time],
        ['Report ID:', report_id, 'Language:', language]
    ]
    
    metadata_table = Table(metadata, colWidths=[1.3*inch, 2*inch, 1.3*inch, 1.9*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Patient information section
    story.append(Paragraph("Patient and Clinic Details", section_header_style))
    
    patient_data = [
        ['Patient Name:', patient_name],
        ['Patient ID:', patient_id],
        ['Age:', f"{age_str} years"],
        ['Gender:', gender],
        ['Referring Physician:', physician_name],
        ['Email:', email],
    ]
    
    patient_table = Table(patient_data, colWidths=[2*inch, 4.5*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # What we found
    story.append(Paragraph("Diagnosis", section_header_style))
    
    diagnosis_data = [
        ['Predicted Disease:', predicted_disease],
        ['Explanation Type:', 'Educational Overview'],
    ]
    
    diagnosis_table = Table(diagnosis_data, colWidths=[2*inch, 4.5*inch])
    diagnosis_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#c62828')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
    ]))
    story.append(diagnosis_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # OCT scan picture
    story.append(Paragraph("OCT Scan Image", section_header_style))
    
    if oct_image_path and os.path.exists(oct_image_path):
        try:
            img = Image(oct_image_path, width=5*inch, height=3.75*inch)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 0.3 * inch))
        except Exception as e:
            story.append(Paragraph(f"<i>OCT image could not be loaded: {str(e)}</i>", body_style))
            story.append(Spacer(1, 0.2 * inch))
    else:
        story.append(Paragraph("<i>OCT scan image not available</i>", body_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # AI-generated explanation
    story.append(Paragraph("Educational Overview", section_header_style))
    
    # Format the explanation nicely
    if explanation_text and explanation_text.strip():
        # Break into lines
        lines = explanation_text.split('\n')
        
        current_section = None
        bullet_items = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty or debug lines
            if not line or line.startswith('['):
                continue
            
            # Is this a heading?
            if line.endswith(':') and len(line) < 60:
                # Print any pending bullets first
                if bullet_items:
                    for item in bullet_items:
                        story.append(Paragraph(f"• {item}", bullet_style))
                    bullet_items = []
                
                # Add section header
                section_style = ParagraphStyle(
                    'SubSection',
                    parent=body_style,
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=colors.HexColor('#424242'),
                    spaceAfter=6,
                    spaceBefore=10
                )
                story.append(Paragraph(line, section_style))
                current_section = line
                
            # Is this a bullet?
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                # Clean it up and save
                clean_line = line.lstrip('•-* ').strip()
                bullet_items.append(clean_line)
                
            # Regular text
            else:
                # Print pending bullets first
                if bullet_items:
                    for item in bullet_items:
                        story.append(Paragraph(f"• {item}", bullet_style))
                    bullet_items = []
                
                # Add paragraph
                story.append(Paragraph(line, body_style))
        
        # Don't forget remaining bullets
        if bullet_items:
            for item in bullet_items:
                story.append(Paragraph(f"• {item}", bullet_style))
    else:
        story.append(Paragraph(
            "<i>Detailed medical analysis is not available. "
            "Please consult with your ophthalmologist for a comprehensive evaluation.</i>",
            body_style
        ))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # What to do next
    story.append(Paragraph("Recommendation", section_header_style))
    
    recommendation_text = """
    Based on the AI analysis of the OCT scan, we recommend:
    """
    story.append(Paragraph(recommendation_text, body_style))
    
    recommendations = [
        "Follow-up consultation with a qualified ophthalmologist for clinical correlation",
        "Additional diagnostic tests if recommended by your physician",
        "Regular monitoring and adherence to prescribed treatment plans",
        "Immediate medical attention if symptoms worsen or new symptoms develop"
    ]
    
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", bullet_style))
    
    story.append(Spacer(1, 0.15 * inch))
    
    important_style = ParagraphStyle(
        'Important',
        parent=body_style,
        fontSize=9,
        textColor=colors.HexColor('#c62828'),
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph(
        "<b>Important:</b> This AI-generated report is for educational and informational purposes only. "
        "It should not replace professional medical diagnosis or treatment. Always consult with a "
        "qualified healthcare provider for proper medical advice.",
        important_style
    ))
    
    story.append(Spacer(1, 0.4 * inch))
    
    # Signature area
    signature_data = [
        ['', ''],
        ['_' * 40, '_' * 40],
        [physician_name, f'Date: {report_date}'],
    ]
    
    signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
    ]))
    story.append(signature_table)
    
    # Bottom of page
    story.append(Spacer(1, 0.3 * inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=body_style,
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    story.append(Paragraph(
        "<i>This report was generated by LuminaPath AI-Powered Retinal Analysis System.<br/>"
        "For clinical interpretation and treatment decisions, please consult with a qualified ophthalmologist.</i>",
        footer_style
    ))
    
    # Create the PDF
    doc.build(story)
    
    return output_path


def generate_report_simple(patient_data: dict, image_path: str, explanation: str) -> str:
    """Simpler way to generate reports (old method)"""
    return generate_medical_report(
        patient_name=patient_data.get('name', 'Unknown Patient'),
        patient_age=patient_data.get('age', 0),
        patient_id=patient_data.get('id', 'UNKNOWN'),
        oct_image_path=image_path,
        explanation_text=explanation,
        predicted_disease=patient_data.get('disease', 'Retinal Condition'),
        gender=patient_data.get('gender', 'Not Specified'),
        physician=patient_data.get('physician', 'Not Specified'),
        email=patient_data.get('email', 'Not Provided')
    )
