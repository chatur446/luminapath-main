"""Sends HTML email reports to patients"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from config import Config


def send_html_report(
    email: str,
    patient_name: str,
    html_content: str,
    method: str = "gmail",
    sender_email: str = None,
    sender_password: str = None
) -> dict:
    """Send HTML report via email (Gmail only for now)"""
    
    if method.lower() == "gmail":
        return send_html_gmail(
            recipient_email=email,
            patient_name=patient_name,
            html_content=html_content,
            sender_email=sender_email,
            sender_password=sender_password
        )
    else:
        return {
            "success": False,
            "message": f"Email method '{method}' not supported. Use 'gmail'."
        }


def send_html_gmail(
    recipient_email: str,
    patient_name: str,
    html_content: str,
    sender_email: str = None,
    sender_password: str = None
) -> dict:
    """Send HTML report via Gmail"""
    try:
        # Use default email settings if none provided
        if sender_email is None:
            sender_email = Config.GMAIL_USER
        if sender_password is None:
            sender_password = Config.GMAIL_APP_PASSWORD
        
        if not sender_email or not sender_password:
            raise ValueError(
                "Email credentials not configured. "
                "Please set GMAIL_USER and GMAIL_APP_PASSWORD in your .env file."
            )
        
        # Build email
        msg = MIMEMultipart('alternative')
        msg['From'] = f"LuminaPath AI System <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"Your Retinal Analysis Report - {patient_name}"
        
        # Plain text fallback
        text_body = f"""Dear {patient_name},

Thank you for using LuminaPath for your retinal analysis.

Your detailed retinal health report is ready. Please view this email in an HTML-capable email client to see the full formatted report.

If you have any questions, please consult with your ophthalmologist for professional medical advice.

Best regards,
LuminaPath Team

---
This is an automated email. Please do not reply directly to this message.
"""
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send it
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {
            "success": True,
            "message": f"Report sent successfully to {recipient_email}"
        }
    
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Gmail authentication failed. Check your email and app password."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Email sending failed: {str(e)}"
        }
