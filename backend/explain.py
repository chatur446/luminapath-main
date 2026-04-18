"""Generates medical explanations and full reports using AI (Gemini + Perplexity backup)"""

import os
import google.generativeai as genai
import google.generativeai
from typing import Optional, Dict, Any
import traceback
import time
import requests
from datetime import datetime

from config import Config

# Main AI: Gemini 1.5 Flash
GEMINI_MODEL = "gemini-1.5-flash"

# Backup AI: Perplexity
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

MAX_RETRIES = 2
USE_PERPLEXITY_FIRST = False

DEBUG_LOGGING = True  # Keep on so you can see what's happening


def log_debug(message: str):
    if DEBUG_LOGGING:
        print(message)


def configure_gemini() -> str:
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return api_key


def get_perplexity_key() -> Optional[str]:
    return os.getenv("PERPLEXITY_API_KEY") or getattr(Config, 'PERPLEXITY_API_KEY', None)


def _get_language_instruction(language: str) -> str:
    """
    Returns a strong native-language instruction telling Gemini to respond in that language.
    Using native script instructions dramatically improves compliance.
    """
    instructions = {
        "Kannada": "ನೀವು ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರಿಸಬೇಕು. ಇಂಗ್ಲಿಷ್ ಬಳಸಬೇಡಿ.",
        "Hindi (India)": "आपको केवल हिंदी में उत्तर देना है। अंग्रेजी का उपयोग न करें।",
        "Hindi": "आपको केवल हिंदी में उत्तर देना है। अंग्रेजी का उपयोग न करें।",
        "Spanish": "Debes responder únicamente en español. No uses inglés.",
        "French": "Vous devez répondre uniquement en français. N'utilisez pas l'anglais.",
        "German": "Sie müssen ausschließlich auf Deutsch antworten. Verwenden Sie kein Englisch.",
        "Arabic": "يجب أن تجيب باللغة العربية فقط. لا تستخدم الإنجليزية.",
        "Chinese (Simplified)": "你必须只用简体中文回答。不要使用英语。",
        "Chinese (Traditional)": "你必須只用繁體中文回答。不要使用英語。",
        "Japanese": "日本語のみで回答してください。英語は使用しないでください。",
        "Korean": "한국어로만 답변해야 합니다. 영어를 사용하지 마세요.",
        "Portuguese": "Você deve responder apenas em português. Não use inglês.",
        "Russian": "Вы должны отвечать только на русском языке. Не используйте английский.",
        "Italian": "Devi rispondere solo in italiano. Non usare l'inglese.",
        "Dutch": "U moet alleen in het Nederlands antwoorden. Gebruik geen Engels.",
        "Turkish": "Yalnızca Türkçe yanıt vermelisiniz. İngilizce kullanmayın.",
        "Tamil": "நீங்கள் தமிழில் மட்டுமே பதிலளிக்க வேண்டும். ஆங்கிலம் பயன்படுத்தாதீர்கள்.",
        "Telugu": "మీరు తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి. ఆంగ్లం వాడవద్దు.",
        "Bengali": "আপনাকে শুধুমাত্র বাংলায় উত্তর দিতে হবে। ইংরেজি ব্যবহার করবেন না।",
        "Marathi": "तुम्ही फक्त मराठीत उत्तर द्यावे. इंग्रजी वापरू नका.",
        "Gujarati": "તમારે માત્ર ગુજરાતીમાં જ જવાબ આપવો જોઈએ. અંગ્રેજી વાપરશો નહીં.",
        "Punjabi": "ਤੁਹਾਨੂੰ ਸਿਰਫ਼ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦੇਣਾ ਚਾਹੀਦਾ ਹੈ। ਅੰਗਰੇਜ਼ੀ ਦੀ ਵਰਤੋਂ ਨਾ ਕਰੋ।",
        "Urdu": "آپ کو صرف اردو میں جواب دینا ہے۔ انگریزی استعمال نہ کریں۔",
        "Vietnamese": "Bạn phải trả lời bằng tiếng Việt. Không sử dụng tiếng Anh.",
        "Thai": "คุณต้องตอบเป็นภาษาไทยเท่านั้น อย่าใช้ภาษาอังกฤษ",
        "Indonesian": "Anda harus menjawab hanya dalam bahasa Indonesia. Jangan gunakan bahasa Inggris.",
        "Malay": "Anda mesti menjawab dalam bahasa Melayu sahaja. Jangan gunakan bahasa Inggeris.",
        "Polish": "Musisz odpowiadać tylko po polsku. Nie używaj angielskiego.",
        "Swedish": "Du måste svara endast på svenska. Använd inte engelska.",
        "Greek": "Πρέπει να απαντάτε μόνο στα ελληνικά. Μην χρησιμοποιείτε αγγλικά.",
        "Hebrew": "עליך להשיב בעברית בלבד. אל תשתמש באנגלית.",
        "Filipino": "Kailangan mong sumagot sa Filipino lamang. Huwag gumamit ng Ingles.",
    }
    native = instructions.get(language, "")
    if native:
        return f"{native}\nYou MUST respond entirely in {language}. Do NOT use English. Do NOT mix languages."
    else:
        return f"You MUST respond entirely in {language}. Do NOT use English. Do NOT mix languages. Every single word must be in {language}."


def _build_prompt(disease_name: str, language: str) -> str:
    """Create the AI prompt with strong language enforcement"""
    lang_instruction = _get_language_instruction(language)

    return f"""{lang_instruction}

Provide an educational overview of the retinal condition called "{disease_name}".

Include:
- Brief description of the condition
- Common signs and symptoms
- General causes or risk factors
- Available treatment approaches

Write everything in {language} only. Do not write a single word in English unless {language} is English."""


def _get_static_fallback(disease_name: str) -> str:
    return f"""Educational Overview of {disease_name}:

{disease_name} is a retinal condition affecting visual function.

Key points:
- Visual symptoms may vary by severity
- Treatment options depend on specific presentation
- Regular ophthalmological monitoring recommended

Consult an ophthalmologist for personalized medical guidance."""


def _call_perplexity(prompt: str, language: str = "English") -> Optional[str]:
    try:
        api_key = get_perplexity_key()
        if not api_key:
            print("[ERROR] PERPLEXITY_API_KEY not set")
            return None

        lang_instruction = _get_language_instruction(language)

        response = requests.post(
            PERPLEXITY_API_URL,
            json={
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are an expert ophthalmology educator. {lang_instruction}"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
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
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            print("[ERROR] No candidates")
            return None

        candidate = response.candidates[0]

        if hasattr(candidate, 'finish_reason'):
            reason = candidate.finish_reason
            print(f"[DEBUG] finish_reason: {reason}")
            if reason in [2, 3]:
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
    try:
        configure_gemini()
        model = genai.GenerativeModel(GEMINI_MODEL)

        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[DEBUG] Gemini attempt {attempt + 1}/{MAX_RETRIES + 1}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,   # Lower temperature = more obedient to instructions
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
    """Get medical explanation in the specified language"""
    print(f"[INFO] get_disease_explanation called — disease={disease_name}, language={language}")

    try:
        prompt = _build_prompt(disease_name, language)
        print(f"[DEBUG] Prompt preview (first 300 chars):\n{prompt[:300]}")

        if USE_PERPLEXITY_FIRST:
            print("[INFO] Using Perplexity (primary)")
            text = _call_perplexity(prompt, language)
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
                print(f"[DEBUG] Explanation preview (first 200 chars):\n{text[:200]}")
                return text
            print("[WARN] Gemini failed, trying Perplexity")
            text = _call_perplexity(prompt, language)
            if text:
                return text

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
    print(f"[INFO] get_disease_explanation_detailed — language={language}")
    try:
        explanation = get_disease_explanation(disease_name, language)
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
    """Generate a complete clinic-grade medical report in the specified language."""
    print(f"[INFO] generate_full_medical_report called — language={language}")

    try:
        configure_gemini()

        report_date = datetime.now().strftime("%B %d, %Y")
        report_time = datetime.now().strftime("%I:%M %p")

        disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease

        lang_instruction = _get_language_instruction(language)

        prompt = f"""{lang_instruction}

You are a professional medical reporting assistant.
Generate a complete medical report for the following patient.
The ENTIRE report — every word, every heading, every label, every sentence — must be written in {language}.
Do NOT use English anywhere in the report unless {language} is English.

PATIENT INFORMATION:
- Name: {patient_name}
- ID: {patient_id}
- Age: {patient_age} years
- Gender: {gender}
- Referring Physician: {physician if physician else 'Not specified'}
- Email: {email}
- Date: {report_date}
- Time: {report_time}

DIAGNOSIS: {disease_display}

MEDICAL BACKGROUND (translate this into {language} in your report):
{explanation_text}

Write the report in {language} with these sections (translate all section names to {language}):
1. Title: "LuminaPath - AI Retinal Analysis Report"
2. Patient Details (as a formatted table)
3. Diagnosis
4. Medical Overview of {disease_display} (description, symptoms, causes, treatment)
5. Recommendations
6. Medical Disclaimer

Use symbols like 📋 🔬 📚 💡 ⚠️ for section headers.
Use bullet points for lists.
Aim for 400-600 words total.
Write ONLY the report. No preamble. No meta-commentary.
Every single word must be in {language}."""

        model = genai.GenerativeModel(GEMINI_MODEL)

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                print(f"[DEBUG] Generating full report attempt {attempt}, language={language}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,   # Lower = more instruction-following
                        max_output_tokens=2048,
                    )
                )

                if response and response.text:
                    report_text = response.text.strip()
                    print(f"[SUCCESS] Report generated ({len(report_text)} chars)")
                    print(f"[DEBUG] Report preview (first 300 chars):\n{report_text[:300]}")
                    return report_text

            except Exception as e:
                print(f"[ERROR] Report generation attempt {attempt} failed: {e}")
                if attempt <= MAX_RETRIES:
                    time.sleep(2)
                    continue

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
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease

    return f"""👁️ LUMINAPATH - AI-POWERED RETINAL ANALYSIS REPORT
Report Language: {language}
Report Date: {report_date} | Time: {report_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PATIENT & CLINIC DETAILS

Patient Name:        {patient_name}
Patient ID:          {patient_id}
Age:                 {patient_age} years
Gender:              {gender}
Email:               {email}
Referring Physician: {physician if physician else 'Not specified'}
Report Language:     {language}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 DIAGNOSIS

Detected Condition: {disease_display}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 MEDICAL OVERVIEW

{explanation_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATION

• Schedule a follow-up with your ophthalmologist
• Discuss treatment options with your physician
• Regular monitoring is essential
• Contact your doctor if symptoms worsen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ MEDICAL DISCLAIMER

This report is AI-generated for educational purposes only.
Always consult a qualified ophthalmologist for diagnosis and treatment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LuminaPath AI System | {report_date} at {report_time}
""""""Generates medical explanations and full reports using AI (Gemini + Perplexity backup)"""

import os
import google.generativeai as genai
import google.generativeai
from typing import Optional, Dict, Any
import traceback
import time
import requests
from datetime import datetime

from config import Config

# Main AI: Gemini 1.5 Flash
GEMINI_MODEL = "gemini-1.5-flash"

# Backup AI: Perplexity
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

MAX_RETRIES = 2
USE_PERPLEXITY_FIRST = False

DEBUG_LOGGING = True  # Keep on so you can see what's happening


def log_debug(message: str):
    if DEBUG_LOGGING:
        print(message)


def configure_gemini() -> str:
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return api_key


def get_perplexity_key() -> Optional[str]:
    return os.getenv("PERPLEXITY_API_KEY") or getattr(Config, 'PERPLEXITY_API_KEY', None)


def _get_language_instruction(language: str) -> str:
    """
    Returns a strong native-language instruction telling Gemini to respond in that language.
    Using native script instructions dramatically improves compliance.
    """
    instructions = {
        "Kannada": "ನೀವು ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರಿಸಬೇಕು. ಇಂಗ್ಲಿಷ್ ಬಳಸಬೇಡಿ.",
        "Hindi (India)": "आपको केवल हिंदी में उत्तर देना है। अंग्रेजी का उपयोग न करें।",
        "Hindi": "आपको केवल हिंदी में उत्तर देना है। अंग्रेजी का उपयोग न करें।",
        "Spanish": "Debes responder únicamente en español. No uses inglés.",
        "French": "Vous devez répondre uniquement en français. N'utilisez pas l'anglais.",
        "German": "Sie müssen ausschließlich auf Deutsch antworten. Verwenden Sie kein Englisch.",
        "Arabic": "يجب أن تجيب باللغة العربية فقط. لا تستخدم الإنجليزية.",
        "Chinese (Simplified)": "你必须只用简体中文回答。不要使用英语。",
        "Chinese (Traditional)": "你必須只用繁體中文回答。不要使用英語。",
        "Japanese": "日本語のみで回答してください。英語は使用しないでください。",
        "Korean": "한국어로만 답변해야 합니다. 영어를 사용하지 마세요.",
        "Portuguese": "Você deve responder apenas em português. Não use inglês.",
        "Russian": "Вы должны отвечать только на русском языке. Не используйте английский.",
        "Italian": "Devi rispondere solo in italiano. Non usare l'inglese.",
        "Dutch": "U moet alleen in het Nederlands antwoorden. Gebruik geen Engels.",
        "Turkish": "Yalnızca Türkçe yanıt vermelisiniz. İngilizce kullanmayın.",
        "Tamil": "நீங்கள் தமிழில் மட்டுமே பதிலளிக்க வேண்டும். ஆங்கிலம் பயன்படுத்தாதீர்கள்.",
        "Telugu": "మీరు తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి. ఆంగ్లం వాడవద్దు.",
        "Bengali": "আপনাকে শুধুমাত্র বাংলায় উত্তর দিতে হবে। ইংরেজি ব্যবহার করবেন না।",
        "Marathi": "तुम्ही फक्त मराठीत उत्तर द्यावे. इंग्रजी वापरू नका.",
        "Gujarati": "તમારે માત્ર ગુજરાતીમાં જ જવાબ આપવો જોઈએ. અંગ્રેજી વાપરશો નહીં.",
        "Punjabi": "ਤੁਹਾਨੂੰ ਸਿਰਫ਼ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦੇਣਾ ਚਾਹੀਦਾ ਹੈ। ਅੰਗਰੇਜ਼ੀ ਦੀ ਵਰਤੋਂ ਨਾ ਕਰੋ।",
        "Urdu": "آپ کو صرف اردو میں جواب دینا ہے۔ انگریزی استعمال نہ کریں۔",
        "Vietnamese": "Bạn phải trả lời bằng tiếng Việt. Không sử dụng tiếng Anh.",
        "Thai": "คุณต้องตอบเป็นภาษาไทยเท่านั้น อย่าใช้ภาษาอังกฤษ",
        "Indonesian": "Anda harus menjawab hanya dalam bahasa Indonesia. Jangan gunakan bahasa Inggris.",
        "Malay": "Anda mesti menjawab dalam bahasa Melayu sahaja. Jangan gunakan bahasa Inggeris.",
        "Polish": "Musisz odpowiadać tylko po polsku. Nie używaj angielskiego.",
        "Swedish": "Du måste svara endast på svenska. Använd inte engelska.",
        "Greek": "Πρέπει να απαντάτε μόνο στα ελληνικά. Μην χρησιμοποιείτε αγγλικά.",
        "Hebrew": "עליך להשיב בעברית בלבד. אל תשתמש באנגלית.",
        "Filipino": "Kailangan mong sumagot sa Filipino lamang. Huwag gumamit ng Ingles.",
    }
    native = instructions.get(language, "")
    if native:
        return f"{native}\nYou MUST respond entirely in {language}. Do NOT use English. Do NOT mix languages."
    else:
        return f"You MUST respond entirely in {language}. Do NOT use English. Do NOT mix languages. Every single word must be in {language}."


def _build_prompt(disease_name: str, language: str) -> str:
    """Create the AI prompt with strong language enforcement"""
    lang_instruction = _get_language_instruction(language)

    return f"""{lang_instruction}

Provide an educational overview of the retinal condition called "{disease_name}".

Include:
- Brief description of the condition
- Common signs and symptoms
- General causes or risk factors
- Available treatment approaches

Write everything in {language} only. Do not write a single word in English unless {language} is English."""


def _get_static_fallback(disease_name: str) -> str:
    return f"""Educational Overview of {disease_name}:

{disease_name} is a retinal condition affecting visual function.

Key points:
- Visual symptoms may vary by severity
- Treatment options depend on specific presentation
- Regular ophthalmological monitoring recommended

Consult an ophthalmologist for personalized medical guidance."""


def _call_perplexity(prompt: str, language: str = "English") -> Optional[str]:
    try:
        api_key = get_perplexity_key()
        if not api_key:
            print("[ERROR] PERPLEXITY_API_KEY not set")
            return None

        lang_instruction = _get_language_instruction(language)

        response = requests.post(
            PERPLEXITY_API_URL,
            json={
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are an expert ophthalmology educator. {lang_instruction}"
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
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
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            print("[ERROR] No candidates")
            return None

        candidate = response.candidates[0]

        if hasattr(candidate, 'finish_reason'):
            reason = candidate.finish_reason
            print(f"[DEBUG] finish_reason: {reason}")
            if reason in [2, 3]:
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
    try:
        configure_gemini()
        model = genai.GenerativeModel(GEMINI_MODEL)

        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[DEBUG] Gemini attempt {attempt + 1}/{MAX_RETRIES + 1}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,   # Lower temperature = more obedient to instructions
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
    """Get medical explanation in the specified language"""
    print(f"[INFO] get_disease_explanation called — disease={disease_name}, language={language}")

    try:
        prompt = _build_prompt(disease_name, language)
        print(f"[DEBUG] Prompt preview (first 300 chars):\n{prompt[:300]}")

        if USE_PERPLEXITY_FIRST:
            print("[INFO] Using Perplexity (primary)")
            text = _call_perplexity(prompt, language)
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
                print(f"[DEBUG] Explanation preview (first 200 chars):\n{text[:200]}")
                return text
            print("[WARN] Gemini failed, trying Perplexity")
            text = _call_perplexity(prompt, language)
            if text:
                return text

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
    print(f"[INFO] get_disease_explanation_detailed — language={language}")
    try:
        explanation = get_disease_explanation(disease_name, language)
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
    """Generate a complete clinic-grade medical report in the specified language."""
    print(f"[INFO] generate_full_medical_report called — language={language}")

    try:
        configure_gemini()

        report_date = datetime.now().strftime("%B %d, %Y")
        report_time = datetime.now().strftime("%I:%M %p")

        disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease

        lang_instruction = _get_language_instruction(language)

        prompt = f"""{lang_instruction}

You are a professional medical reporting assistant.
Generate a complete medical report for the following patient.
The ENTIRE report — every word, every heading, every label, every sentence — must be written in {language}.
Do NOT use English anywhere in the report unless {language} is English.

PATIENT INFORMATION:
- Name: {patient_name}
- ID: {patient_id}
- Age: {patient_age} years
- Gender: {gender}
- Referring Physician: {physician if physician else 'Not specified'}
- Email: {email}
- Date: {report_date}
- Time: {report_time}

DIAGNOSIS: {disease_display}

MEDICAL BACKGROUND (translate this into {language} in your report):
{explanation_text}

Write the report in {language} with these sections (translate all section names to {language}):
1. Title: "LuminaPath - AI Retinal Analysis Report"
2. Patient Details (as a formatted table)
3. Diagnosis
4. Medical Overview of {disease_display} (description, symptoms, causes, treatment)
5. Recommendations
6. Medical Disclaimer

Use symbols like 📋 🔬 📚 💡 ⚠️ for section headers.
Use bullet points for lists.
Aim for 400-600 words total.
Write ONLY the report. No preamble. No meta-commentary.
Every single word must be in {language}."""

        model = genai.GenerativeModel(GEMINI_MODEL)

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                print(f"[DEBUG] Generating full report attempt {attempt}, language={language}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,   # Lower = more instruction-following
                        max_output_tokens=2048,
                    )
                )

                if response and response.text:
                    report_text = response.text.strip()
                    print(f"[SUCCESS] Report generated ({len(report_text)} chars)")
                    print(f"[DEBUG] Report preview (first 300 chars):\n{report_text[:300]}")
                    return report_text

            except Exception as e:
                print(f"[ERROR] Report generation attempt {attempt} failed: {e}")
                if attempt <= MAX_RETRIES:
                    time.sleep(2)
                    continue

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
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease

    return f"""👁️ LUMINAPATH - AI-POWERED RETINAL ANALYSIS REPORT
Report Language: {language}
Report Date: {report_date} | Time: {report_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PATIENT & CLINIC DETAILS

Patient Name:        {patient_name}
Patient ID:          {patient_id}
Age:                 {patient_age} years
Gender:              {gender}
Email:               {email}
Referring Physician: {physician if physician else 'Not specified'}
Report Language:     {language}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 DIAGNOSIS

Detected Condition: {disease_display}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 MEDICAL OVERVIEW

{explanation_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATION

• Schedule a follow-up with your ophthalmologist
• Discuss treatment options with your physician
• Regular monitoring is essential
• Contact your doctor if symptoms worsen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ MEDICAL DISCLAIMER

This report is AI-generated for educational purposes only.
Always consult a qualified ophthalmologist for diagnosis and treatment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LuminaPath AI System | {report_date} at {report_time}
"""