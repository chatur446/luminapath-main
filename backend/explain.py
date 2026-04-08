"""Generates medical explanations and full reports using AI (Gemini + Perplexity backup)"""

import os
import google.generativeai as genai
from typing import Optional, Dict, Any
import traceback
import time
import requests
from datetime import datetime

from config import Config

# Main AI: Gemini 2.5 Flash
GEMINI_MODEL = "models/gemini-2.5-flash"

# Backup AI: Perplexity
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

MAX_RETRIES = 2
USE_PERPLEXITY_FIRST = False  # True = use Perplexity as main AI

# Turn on for debugging
DEBUG_LOGGING = False


def log_debug(message: str):
    """Print debug info if turned on"""
    if DEBUG_LOGGING:
        print(message)


def configure_gemini() -> str:
    """Set up Gemini AI"""
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return api_key


def get_perplexity_key() -> Optional[str]:
    """Get Perplexity API key"""
    return os.getenv("PERPLEXITY_API_KEY") or getattr(Config, 'PERPLEXITY_API_KEY', None)


def _build_prompt(disease_name: str, language: str) -> str:
    """Create the AI prompt"""
    return f"""You are an educational ophthalmology assistant. Provide an informational overview of the retinal condition called "{disease_name}" in {language}.

Include:
- Brief description of the condition
- Common signs and symptoms
- General causes or risk factors
- Available treatment approaches

Keep it educational and professional. This is for healthcare training purposes."""


def _get_static_fallback(disease_name: str) -> str:
    """Basic info when AI fails"""
    return f"""Educational Overview of {disease_name}:

{disease_name} is a retinal condition affecting visual function. 

Key points:
- Visual symptoms may vary by severity
- Treatment options depend on specific presentation
- Regular ophthalmological monitoring recommended

Consult an ophthalmologist for personalized medical guidance."""


def _call_perplexity(prompt: str) -> Optional[str]:
    """Ask Perplexity AI"""
    try:
        api_key = get_perplexity_key()
        if not api_key:
            print("[ERROR] PERPLEXITY_API_KEY not set")
            return None
        
        print(f"[DEBUG] Calling Perplexity: {PERPLEXITY_MODEL}")
        
        response = requests.post(
            PERPLEXITY_API_URL,
            json={
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert ophthalmology educator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            text = data["choices"][0]["message"]["content"]
            print(f"[SUCCESS] Perplexity: {len(text)} chars")
            return text
        
        return None
            
    except Exception as e:
        print(f"[ERROR] Perplexity failed: {e}")
        return None


def _extract_gemini_text(response) -> Optional[str]:
    """Pull text from Gemini response"""
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            print("[ERROR] No candidates")
            return None
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            reason = candidate.finish_reason
            print(f"[DEBUG] finish_reason: {reason}")
            if reason in [2, 3]:  # Blocked or safety
                print(f"[ERROR] Content blocked (reason={reason})")
                return None
        
        if not hasattr(candidate, 'content') or not candidate.content:
            print("[ERROR] No content")
            return None
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            print("[ERROR] No parts")
            return None
        
        part = candidate.content.parts[0]
        if not hasattr(part, 'text'):
            print("[ERROR] No text attribute")
            return None
        
        text = part.text
        if not text or len(text.strip()) == 0:
            print("[ERROR] Empty text")
            return None
        
        print(f"[SUCCESS] Extracted {len(text)} chars")
        return text
        
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return None


def _call_gemini(prompt: str) -> Optional[str]:
    """Ask Gemini AI (with retry logic)"""
    try:
        configure_gemini()
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[DEBUG] Gemini attempt {attempt + 1}/{MAX_RETRIES + 1}")
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=1024,
                        top_p=0.95,
                        top_k=40,
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                )
                
                text = _extract_gemini_text(response)
                if text:
                    return text
                
                if attempt < MAX_RETRIES:
                    print(f"[WARN] Retry in 2s...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"[ERROR] Gemini exception: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2)
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Gemini setup failed: {e}")
        return None


def get_disease_explanation(disease_name: str, language: str = "English") -> str:
    """Get medical explanation - always returns something"""
    try:
        prompt = _build_prompt(disease_name, language)
        
        # Try primary API
        if USE_PERPLEXITY_FIRST:
            print("[INFO] Using Perplexity (primary)")
            text = _call_perplexity(prompt)
            if text:
                return text
            print("[WARN] Perplexity failed, trying Gemini")
            text = _call_gemini(prompt)
            if text:
                return text
        else:
            print("[INFO] Using Gemini (primary)")
            text = _call_gemini(prompt)
            if text:
                return text
            print("[WARN] Gemini failed, trying Perplexity")
            text = _call_perplexity(prompt)
            if text:
                return text
        
        # Final fallback
        print("[WARN] All APIs failed, using static fallback")
        return _get_static_fallback(disease_name)
        
    except Exception as e:
        print(f"[ERROR] get_disease_explanation: {e}")
        traceback.print_exc()
        return _get_static_fallback(disease_name)


def get_disease_explanation_detailed(
    disease_name: str,
    language: str = "English",
    model_version: str = None
) -> Dict[str, Any]:
    """Get explanation with extra metadata"""
    try:
        # Get explanation
        explanation = get_disease_explanation(disease_name, language)
        
        # Figure out which AI we used
        api_used = "gemini" if not USE_PERPLEXITY_FIRST else "perplexity"
        
        return {
            "disease": disease_name,
            "language": language,
            "explanation": explanation,
            "model": model_version or GEMINI_MODEL,
            "api_used": api_used,
            "success": True
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] get_disease_explanation_detailed: {error_msg}")
        traceback.print_exc()
        
        return {
            "disease": disease_name,
            "language": language,
            "explanation": _get_static_fallback(disease_name),
            "model": model_version or GEMINI_MODEL,
            "api_used": "fallback",
            "success": False,
            "error": error_msg
        }


def generate_full_medical_report(
    patient_name: str,
    patient_age: str,
    patient_id: str,
    gender: str,
    physician: str,
    email: str,
    predicted_disease: str,
    explanation_text: str,
    language: str = "English"
) -> str:
    """
    Generate a complete, clinic-grade medical report using Gemini.
    Returns formatted text ready for display and email.
    """
    try:
        configure_gemini()
        
        # Get current date/time
        report_date = datetime.now().strftime("%B %d, %Y")
        report_time = datetime.now().strftime("%I:%M %p")
        
        # Extract clean disease name
        disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease
        
        # Build comprehensive prompt for Gemini
        prompt = f"""You are a professional medical reporting assistant creating a clinic-grade educational retinal analysis report.

PATIENT INFORMATION:
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Age: {patient_age} years
- Gender: {gender}
- Referring Physician: {physician if physician else 'Not specified'}
- Email: {email}
- Report Date: {report_date}
- Report Time: {report_time}
- Report Language: {language}

DIAGNOSIS:
Detected Condition: {disease_display}

BASE MEDICAL INFORMATION:
{explanation_text}

TASK:
Create a complete, professional medical report in {language}. Format it like a real clinic report with clear sections and professional medical language. Include:

1. **Title Section**: "LuminaPath - AI-Powered Retinal Analysis Report"

2. **Patient & Clinic Details**: Format as a clean table with all patient information

3. **Diagnosis Section**: State the detected condition clearly

4. **Medical Overview**: Provide a comprehensive educational overview of {disease_display} including:
   - What this condition is and how it affects the retina
   - Common signs and symptoms patients may experience
   - Why this condition develops (causes and risk factors)
   - How the condition typically progresses (prognosis)
   - Available treatment approaches and management options
   - Prevention strategies if applicable

5. **Recommendation Section**: Provide clear, actionable next steps:
   - Schedule follow-up with ophthalmologist
   - Specific tests or monitoring recommended
   - Lifestyle modifications if relevant
   - When to seek immediate care

6. **Medical Disclaimer**: Include a professional disclaimer that this is an AI-assisted educational tool and patients should consult their ophthalmologist for diagnosis and treatment.

IMPORTANT FORMATTING RULES:
- Use clear headings with symbols (📋, 🔬, 📚, 💡, ⚠️)
- Use bullet points for lists
- Write in professional medical language but keep it patient-friendly
- NO placeholders or generic phrases like "consult your doctor"
- Be specific and educational
- Make it look like a real medical report from Mayo Clinic or Johns Hopkins
- Total report should be comprehensive but readable (aim for 400-600 words)

Return ONLY the formatted medical report text. Do not include any preamble or explanations."""

        # Call Gemini with retries
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                print(f"[DEBUG] Generating full report, attempt {attempt}")
                response = model.generate_content(prompt)
                
                if response and response.text:
                    report_text = response.text.strip()
                    print(f"✅ Full medical report generated ({len(report_text)} chars)")
                    return report_text
                    
            except Exception as e:
                print(f"[ERROR] Gemini report generation attempt {attempt} failed: {e}")
                if attempt <= MAX_RETRIES:
                    time.sleep(2)
                    continue
        
        # Fallback: Generate structured report manually
        print("[WARN] Using fallback report generation")
        return _generate_fallback_report(
            patient_name, patient_age, patient_id, gender, physician, email,
            predicted_disease, explanation_text, language, report_date, report_time
        )
        
    except Exception as e:
        print(f"[ERROR] generate_full_medical_report: {e}")
        traceback.print_exc()
        return _generate_fallback_report(
            patient_name, patient_age, patient_id, gender, physician, email,
            predicted_disease, explanation_text, language,
            datetime.now().strftime("%B %d, %Y"),
            datetime.now().strftime("%I:%M %p")
        )


def _generate_fallback_report(
    patient_name: str, patient_age: str, patient_id: str, gender: str,
    physician: str, email: str, predicted_disease: str, explanation_text: str,
    language: str, report_date: str, report_time: str
) -> str:
    """Generate a structured report when Gemini fails"""
    
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease
    
    return f"""👁️ LUMINAPATH - AI-POWERED RETINAL ANALYSIS REPORT

Report Date: {report_date} | Time: {report_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PATIENT & CLINIC DETAILS

Patient Name:       {patient_name}
Patient ID:         {patient_id}
Age:                {patient_age} years
Gender:             {gender}
Email:              {email}
Referring Physician: {physician if physician else 'Not specified'}
Report Language:    {language}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 DIAGNOSIS

Detected Condition: {disease_display}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 MEDICAL OVERVIEW

{explanation_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATION

Next Steps:
• Schedule a comprehensive follow-up appointment with your ophthalmologist
• Discuss this report and explore appropriate treatment options
• Regular monitoring is essential for optimal eye health and early intervention
• Contact your doctor immediately if you experience worsening visual symptoms
• Maintain detailed records of any vision changes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ MEDICAL DISCLAIMER

This report is generated by an AI-assisted diagnostic tool and is intended to provide 
educational information to aid medical professionals. It should NOT be used as the sole 
basis for medical diagnosis or treatment decisions. Always consult with a qualified 
ophthalmologist or healthcare provider for professional medical advice, diagnosis, and 
personalized treatment recommendations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LuminaPath AI System
Making retinal healthcare accessible through AI
Report generated on {report_date} at {report_time}
"""
