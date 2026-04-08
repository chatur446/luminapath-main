"""Main API server for LuminaPath"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import shutil
import numpy as np
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import io

from config import Config
from model_loader import load_model, preprocess_image, get_disease_name
from explain import get_disease_explanation_detailed, generate_full_medical_report
from html_report_generator import generate_html_report, generate_text_report
from email_sender import send_html_report

app = FastAPI(title="LuminaPath API", version="1.0.0")

# For CPU-heavy tasks (predictions)
executor = ThreadPoolExecutor(max_workers=2)

@app.on_event("startup")
async def startup_event():
    """Load model when server starts"""
    try:
        model = load_model()
        print(f"✅ Model preloaded successfully with input shape: {model.input_shape}")
    except Exception as e:
        print(f"⚠️ Warning: Could not preload model: {e}")

# Let frontend talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# What the model's 8 outputs mean
CLASS_LABELS = [
    "Class_1",  # AMD
    "Class_2",  # CNV
    "Class_3",  # CSR
    "Class_4",  # DME
    "Class_5",  # DR
    "Class_6",  # DRUSEN
    "Class_7",  # MH
    "Class_8"   # NORMAL
]

# Make sure folder exists
UPLOAD_DIR = Config.UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _run_prediction(image_bytes, content_type):
    """Run AI prediction (CPU-heavy, so runs in thread pool)"""
    try:
        # Check file type
        if not content_type.startswith('image/'):
            raise ValueError("File must be an image")
        
        # Load model
        model = load_model()
        
        # Prepare image (no file saving needed)
        processed_image = preprocess_image(io.BytesIO(image_bytes))
        
        # Get prediction
        predictions = model.predict(processed_image, verbose=0)
        
        # Find best match
        predicted_index = np.argmax(predictions[0])
        predicted_class = CLASS_LABELS[predicted_index]
        
        # Turn into readable name
        disease_name = get_disease_name(predicted_class)
        
        return disease_name
    
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Analyze OCT scan and return disease prediction"""
    try:
        # Read file
        image_bytes = await file.read()
        
        # Run AI (with timeout)
        loop = asyncio.get_event_loop()
        disease_name = await asyncio.wait_for(
            loop.run_in_executor(executor, _run_prediction, image_bytes, file.content_type),
            timeout=10.0
        )
        
        # Return only the disease name
        return {
            "predicted_class": disease_name
        }
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Prediction timeout: Model took too long to respond")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/")
async def root():
    """Check if server is running"""
    return {
        "status": "LuminaPath API is running",
        "version": "1.0.0",
        "config": {
            "gemini_configured": bool(Config.GEMINI_API_KEY),
            "email_configured": bool(Config.GMAIL_USER or Config.SENDGRID_API_KEY),
            "model_path": str(Config.MODEL_PATH)
        }
    }


# Pydantic models for request validation
class ExplainRequest(BaseModel):
    disease_name: str
    language: str = "English"


class PDFRequest(BaseModel):
    patient_name: str
    patient_age: int
    patient_id: str
    explanation: str


class ReportRequest(BaseModel):
    """Request model for HTML report generation"""
    patient_name: str
    patient_age: str
    patient_id: str
    explanation: str
    predicted_disease: str
    gender: str
    physician: str = ""
    email: str
    language: str = "English"


class EmailRequest(BaseModel):
    recipient_email: EmailStr
    patient_name: str
    patient_age: str
    patient_id: str
    gender: str
    physician: str
    email: str
    predicted_disease: str
    explanation: str
    language: str
    method: str = "gmail"


@app.post("/explain")
async def explain_disease(request: ExplainRequest):
    """Generate medical explanation using AI"""
    try:
        result = get_disease_explanation_detailed(
            disease_name=request.disease_name,
            language=request.language
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "disease": result["disease"],
            "explanation": result["explanation"],
            "language": result["language"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@app.post("/generate-full-report")
async def generate_full_report_endpoint(request: ReportRequest):
    """Generate complete clinic-grade medical report using Gemini AI"""
    try:
        # Generate full medical report using Gemini
        full_report = generate_full_medical_report(
            patient_name=request.patient_name,
            patient_age=request.patient_age,
            patient_id=request.patient_id,
            gender=request.gender,
            physician=request.physician,
            email=request.email,
            predicted_disease=request.predicted_disease,
            explanation_text=request.explanation,
            language=request.language
        )
        
        print(f"✅ Full medical report generated for {request.patient_name}\n")
        
        return {
            "success": True,
            "report": full_report,
            "message": "Complete medical report generated successfully"
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Full Report Generation Error:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """Generate formatted HTML/text medical report"""
    try:
        # Generate HTML report
        html_report = generate_html_report(
            patient_name=request.patient_name,
            patient_age=request.patient_age,
            patient_id=request.patient_id,
            gender=request.gender,
            physician=request.physician,
            email=request.email,
            predicted_disease=request.predicted_disease,
            explanation=request.explanation,
            language=request.language
        )
        
        # Generate plain text version
        text_report = generate_text_report(
            patient_name=request.patient_name,
            patient_age=request.patient_age,
            patient_id=request.patient_id,
            gender=request.gender,
            physician=request.physician,
            email=request.email,
            predicted_disease=request.predicted_disease,
            explanation=request.explanation,
            language=request.language
        )
        
        print(f"✅ Report generated successfully for {request.patient_name}\n")
        
        return {
            "success": True,
            "html_report": html_report,
            "text_report": text_report,
            "message": "Medical report generated successfully"
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Report Generation Error:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


def convert_markdown_report_to_html(markdown_report: str, patient_name: str, patient_id: str) -> str:
    """Convert Markdown report to professional HTML email"""
    import re
    from datetime import datetime
    
    # Split report into lines
    lines = markdown_report.split('\n')
    html_parts = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append('<br/>')
            continue
        
        # Handle headers
        if line.startswith('###'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            text = line.replace('###', '').strip()
            html_parts.append(f'<h3 style="color: #1e88e5; margin-top: 25px; margin-bottom: 12px; font-size: 18px;">{text}</h3>')
        elif line.startswith('##'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            text = line.replace('##', '').strip()
            html_parts.append(f'<h2 style="color: #0d47a1; margin-top: 30px; margin-bottom: 15px; font-size: 22px; border-bottom: 2px solid #1e88e5; padding-bottom: 8px;">{text}</h2>')
        elif line.startswith('#'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            text = line.replace('#', '').strip()
            html_parts.append(f'<h1 style="color: #0d47a1; margin-top: 20px; margin-bottom: 15px; font-size: 26px;">{text}</h1>')
        
        # Handle horizontal rules
        elif line.startswith('---') or line.startswith('***'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append('<hr style="border: none; border-top: 2px solid #e0e0e0; margin: 20px 0;"/>')
        
        # Handle bullet points
        elif line.startswith('*') or line.startswith('-'):
            text = re.sub(r'^[\*\-]\s*', '', line)
            # Convert **bold** to <b>
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            # Convert *italic* to <i>
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            
            if not in_list:
                html_parts.append('<ul style="margin-left: 20px; margin-bottom: 15px; line-height: 1.8;">')
                in_list = True
            html_parts.append(f'<li style="margin-bottom: 8px; color: #333;">{text}</li>')
        
        # Handle key-value pairs (e.g., "Patient Name: John")
        elif ':' in line and not line.endswith(':'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            parts = line.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            # Convert **bold** to <b>
            key = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', key)
            value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
            html_parts.append(f'<p style="margin: 8px 0; line-height: 1.6;"><b style="color: #1e88e5;">{key}:</b> {value}</p>')
        
        # Regular paragraphs
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            # Convert **bold** to <b>
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            # Convert *italic* to <i>
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            html_parts.append(f'<p style="margin: 10px 0; line-height: 1.7; color: #333;">{text}</p>')
    
    # Close any open list
    if in_list:
        html_parts.append('</ul>')
    
    # Build complete HTML
    html_body = '\n'.join(html_parts)
    
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuminaPath Medical Report - {patient_name}</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #000000; margin: 0; padding: 0; background-color: #f5f7fa;">
    <div style="max-width: 700px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%); color: white; padding: 30px 40px; text-align: center;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 600; color: #ffffff;">👁️ LuminaPath</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; color: #e3f2fd;">AI-Powered Retinal Analysis Report</p>
            <p style="margin: 15px 0 0 0; font-size: 14px; color: #bbdefb;">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <!-- Report Content -->
        <div style="padding: 40px;">
            {html_body}
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f5f7fa; padding: 25px 40px; border-top: 2px solid #e0e0e0; text-align: center;">
            <p style="margin: 0; font-size: 13px; color: #666; font-style: italic;">
                This report was generated by LuminaPath AI-Powered Retinal Analysis System.<br/>
                For clinical interpretation and treatment decisions, please consult with a qualified ophthalmologist.
            </p>
            <p style="margin: 15px 0 0 0; font-size: 12px; color: #999;">
                © {datetime.now().year} LuminaPath. All rights reserved.
            </p>
        </div>
        
    </div>
</body>
</html>
    """
    
    return full_html


@app.post("/send-report")
async def send_report_email(request: EmailRequest):
    """Send full medical report via email"""
    try:
        # Generate full medical report using Gemini
        full_report = generate_full_medical_report(
            patient_name=request.patient_name,
            patient_age=request.patient_age,
            patient_id=request.patient_id,
            gender=request.gender,
            physician=request.physician,
            email=request.email,
            predicted_disease=request.predicted_disease,
            explanation_text=request.explanation,
            language=request.language
        )
        
        # Convert Markdown report to clean HTML
        html_content = convert_markdown_report_to_html(
            markdown_report=full_report,
            patient_name=request.patient_name,
            patient_id=request.patient_id
        )
        
        result = send_html_report(
            email=request.recipient_email,
            patient_name=request.patient_name,
            html_content=html_content,
            method=request.method
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")
