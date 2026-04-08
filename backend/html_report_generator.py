"""Generates formatted HTML medical reports"""

from datetime import datetime
from typing import Optional


def generate_html_report(
    patient_name: str,
    patient_age: str,
    patient_id: str,
    gender: str,
    physician: str,
    email: str,
    predicted_disease: str,
    explanation: str,
    language: str = "English"
) -> str:
    """
    Generate a clean, formatted HTML medical report.
    Returns HTML string ready for display or email.
    """
    
    # Get current date/time
    report_date = datetime.now().strftime("%B %d, %Y")
    report_time = datetime.now().strftime("%I:%M %p")
    
    # Extract disease name (remove prefix like "CNV - ")
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #000000;
            max-width: 850px;
            margin: 0 auto;
            padding: 30px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        .report-container {{
            background: white;
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
            border-left: 6px solid #1e88e5;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1e88e5;
            padding-bottom: 20px;
            margin-bottom: 35px;
        }}
        .header h1 {{
            color: #0d47a1;
            margin: 0;
            font-size: 32px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            color: #1976d2;
            margin: 8px 0;
            font-size: 16px;
            font-weight: 500;
        }}
        .header .meta {{
            color: #666;
            margin: 8px 0;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            color: #0d47a1;
            padding: 12px 18px;
            font-size: 19px;
            font-weight: 600;
            border-radius: 8px;
            margin-bottom: 18px;
            border-left: 4px solid #1e88e5;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            border-radius: 8px;
            overflow: hidden;
        }}
        .info-table td {{
            padding: 12px 15px;
            border: 1px solid #e0e0e0;
        }}
        .info-table td:first-child {{
            background-color: #f5f5f5;
            font-weight: 600;
            width: 35%;
            color: #1976d2;
        }}
        .info-table td:last-child {{
            background-color: #fafafa;
        }}
        .diagnosis-box {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-left: 5px solid #ff9800;
            padding: 18px;
            margin: 18px 0;
            font-size: 17px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(255,152,0,0.15);
        }}
        .diagnosis-box strong {{
            color: #e65100;
            font-size: 19px;
            display: block;
            margin-bottom: 8px;
        }}
        .content {{
            padding: 15px 20px;
            text-align: justify;
            background: #fafafa;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .content h3 {{
            color: #0d47a1;
            margin-top: 22px;
            margin-bottom: 12px;
            font-size: 18px;
            font-weight: 600;
        }}
        .content ul {{
            margin-left: 25px;
            margin-top: 12px;
        }}
        .content li {{
            margin-bottom: 10px;
            line-height: 1.8;
            color: #212121;
        }}
        .content li::marker {{
            color: #1e88e5;
            font-weight: bold;
        }}
        .recommendation {{
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border-left: 5px solid #4caf50;
            padding: 18px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(76,175,80,0.15);
        }}
        .recommendation h3 {{
            color: #2e7d32;
            margin-top: 0;
            font-size: 18px;
        }}
        .recommendation ul {{
            margin: 12px 0;
            padding-left: 25px;
        }}
        .recommendation li {{
            color: #1b5e20;
            margin-bottom: 10px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 25px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            font-size: 13px;
            color: #666;
        }}
        .disclaimer {{
            background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
            border: 2px solid #fbc02d;
            border-radius: 8px;
            padding: 18px;
            margin-top: 25px;
            font-size: 13px;
            color: #f57f17;
            box-shadow: 0 2px 8px rgba(251,192,45,0.2);
        }}
        .disclaimer strong {{
            color: #e65100;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>👁️ LuminaPath</h1>
            <p class="subtitle">AI-Powered Retinal Analysis Report</p>
            <p class="meta"><strong>Generated:</strong> {report_date} at {report_time}</p>
        </div>

        <div class="section">
            <div class="section-title">📋 Patient & Clinic Details</div>
            <table class="info-table">
                <tr>
                    <td>Patient Name</td>
                    <td>{patient_name}</td>
                </tr>
                <tr>
                    <td>Patient ID</td>
                    <td>{patient_id}</td>
                </tr>
                <tr>
                    <td>Age</td>
                    <td>{patient_age} years</td>
                </tr>
                <tr>
                    <td>Gender</td>
                    <td>{gender}</td>
                </tr>
            <tr>
                <td>Email</td>
                <td>{email}</td>
            </tr>
            <tr>
                <td>Referring Physician</td>
                <td>{physician if physician else 'Not specified'}</td>
            </tr>
            <tr>
                <td>Report Language</td>
                <td>{language}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">🔬 Diagnosis</div>
        <div class="diagnosis-box">
            <strong>Detected Condition:</strong> {disease_display}
        </div>
    </div>

    <div class="section">
        <div class="section-title">📚 Medical Overview</div>
        <div class="content">
            {format_explanation_as_html(explanation)}
        </div>
    </div>

        <div class="section">
            <div class="section-title">💡 Recommendations</div>
            <div class="recommendation">
                <h3>Next Steps:</h3>
                <ul>
                    <li>Schedule a follow-up appointment with your ophthalmologist</li>
                    <li>Discuss this report and your treatment options</li>
                    <li>Regular monitoring is essential for optimal eye health</li>
                    <li>Contact your doctor immediately if you experience worsening symptoms</li>
                </ul>
            </div>
        </div>

        <div class="disclaimer">
            <strong>⚠️ Medical Disclaimer:</strong> This report is generated by an AI-assisted diagnostic tool and is intended to aid medical professionals. It should NOT be used as the sole basis for medical diagnosis or treatment decisions. Always consult with a qualified ophthalmologist or healthcare provider for professional medical advice, diagnosis, and treatment.
        </div>

        <div class="footer">
            <p><strong>LuminaPath AI System</strong></p>
            <p>Making retinal healthcare accessible through AI</p>
            <p>Report generated on {report_date} at {report_time}</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html.strip()


def format_explanation_as_html(explanation: str) -> str:
    """Convert plain text explanation to formatted HTML"""
    if not explanation:
        return "<p>No detailed explanation available.</p>"
    
    # Split into lines
    lines = explanation.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            continue
        
        # Check if it's a header (ends with : and is short)
        if line.endswith(':') and len(line) < 50:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<h3>{line[:-1]}</h3>')
        
        # Check if it's a bullet point
        elif line.startswith(('- ', '• ', '* ')):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            bullet_text = line[2:].strip()
            formatted_lines.append(f'<li>{bullet_text}</li>')
        
        # Regular paragraph
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<p>{line}</p>')
    
    # Close any remaining list
    if in_list:
        formatted_lines.append('</ul>')
    
    return '\n'.join(formatted_lines)


def generate_text_report(
    patient_name: str,
    patient_age: str,
    patient_id: str,
    gender: str,
    physician: str,
    email: str,
    predicted_disease: str,
    explanation: str,
    language: str = "English"
) -> str:
    """Generate plain text version of the report for download"""
    
    report_date = datetime.now().strftime("%B %d, %Y")
    report_time = datetime.now().strftime("%I:%M %p")
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease
    
    text = f"""
================================================================================
                        👁️ LUMINAPATH
            AI-Powered Retinal Analysis Report
================================================================================

Report Date: {report_date}
Report Time: {report_time}

================================================================================
PATIENT & CLINIC DETAILS
================================================================================

Patient Name:       {patient_name}
Patient ID:         {patient_id}
Age:                {patient_age} years
Gender:             {gender}
Email:              {email}
Physician:          {physician if physician else 'Not specified'}
Report Language:    {language}

================================================================================
DIAGNOSIS
================================================================================

Detected Condition: {disease_display}

================================================================================
MEDICAL OVERVIEW
================================================================================

{explanation}

================================================================================
RECOMMENDATION
================================================================================

Next Steps:
- Schedule a follow-up appointment with your ophthalmologist
- Discuss this report and your treatment options
- Regular monitoring is essential for optimal eye health
- Contact your doctor immediately if you experience worsening symptoms

================================================================================
MEDICAL DISCLAIMER
================================================================================

This report is generated by an AI-assisted diagnostic tool and is intended
to aid medical professionals. It should NOT be used as the sole basis for
medical diagnosis or treatment decisions. Always consult with a qualified
ophthalmologist or healthcare provider for professional medical advice,
diagnosis, and treatment.

================================================================================
LuminaPath AI System
Making retinal healthcare accessible through AI
Report generated on {report_date} at {report_time}
================================================================================
    """
    
    return text.strip()
