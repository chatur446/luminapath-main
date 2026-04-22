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

DEBUG_LOGGING = True


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


def _get_system_instruction(language: str) -> str:
    """
    ✅ FIX: Build a system-level instruction for Gemini.
    Passing language rules here (system role) is far more effective
    than embedding them only in the user prompt.
    """
    lang_instruction = _get_language_instruction(language)
    return (
        f"You are an expert ophthalmology medical report writer. "
        f"{lang_instruction} "
        f"All your responses must be written exclusively in {language}. "
        f"Never switch to English unless {language} is English."
    )


def _build_prompt(disease_name: str, language: str) -> str:
    """Create the user-turn prompt. Language enforcement is now in system_instruction."""
    return f"""Provide an educational overview of the retinal condition called "{disease_name}".

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


# ✅ FIX: _call_gemini now accepts `language` and uses system_instruction
def _call_gemini(prompt: str, language: str = "English") -> Optional[str]:
    try:
        configure_gemini()

        # ✅ KEY FIX: Pass language as system_instruction to Gemini
        # This is the most reliable way to enforce language output
        system_instruction = _get_system_instruction(language)

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction   # ← THIS is what was missing
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[DEBUG] Gemini attempt {attempt + 1}/{MAX_RETRIES + 1}, language={language}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,        # Even lower = more obedient
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
            text = _call_gemini(prompt, language)   # ✅ pass language
            if text:
                return text
        else:
            print("[INFO] Using Gemini (primary)")
            text = _call_gemini(prompt, language)   # ✅ pass language
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

        # ✅ FIX: System instruction carries language enforcement for the full report too
        system_instruction = _get_system_instruction(language)

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction   # ← THIS is what was missing
        )

        # User-turn prompt (language rule is in system, so keep this clean)
        prompt = f"""Generate a complete medical report for the following patient.
The ENTIRE report — every word, every heading, every label, every sentence — must be written in {language}.
Do NOT use English anywhere unless {language} is English.

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
Write ONLY the report content. No preamble. No meta-commentary.
Every single word must be in {language}."""

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                print(f"[DEBUG] Generating full report attempt {attempt}, language={language}")

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,        # Lower = more instruction-following
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


# ✅ FIX: Fallback report now uses translated section headers per language
def _generate_fallback_report(
    patient_name: str, patient_age: str, patient_id: str, gender: str,
    physician: str, email: str, predicted_disease: str, explanation_text: str,
    language: str, report_date: str, report_time: str
) -> str:
    disease_display = predicted_disease.split(" - ")[-1] if " - " in predicted_disease else predicted_disease

    # Translated section headers & labels for common languages
    translations = {
        "Kannada": {
            "title": "ಲುಮಿನಾಪಾತ್ - AI ರೆಟಿನಲ್ ವಿಶ್ಲೇಷಣಾ ವರದಿ",
            "report_lang": "ವರದಿ ಭಾಷೆ",
            "report_date": "ವರದಿ ದಿನಾಂಕ",
            "patient_details": "ರೋಗಿಯ ಮತ್ತು ಚಿಕಿತ್ಸಾಲಯ ವಿವರಗಳು",
            "patient_name": "ರೋಗಿಯ ಹೆಸರು",
            "patient_id": "ರೋಗಿಯ ID",
            "age": "ವಯಸ್ಸು",
            "gender": "ಲಿಂಗ",
            "email": "ಇಮೇಲ್",
            "physician": "ಉಲ್ಲೇಖ ವೈದ್ಯ",
            "diagnosis": "ರೋಗನಿರ್ಣಯ",
            "detected": "ಪತ್ತೆಯಾದ ಸ್ಥಿತಿ",
            "overview": "ವೈದ್ಯಕೀಯ ಅವಲೋಕನ",
            "recommendations": "ಶಿಫಾರಸುಗಳು",
            "rec1": "ನಿಮ್ಮ ನೇತ್ರತಜ್ಞರೊಂದಿಗೆ ಫಾಲೋ-ಅಪ್ ನಿಗದಿಪಡಿಸಿ",
            "rec2": "ನಿಮ್ಮ ವೈದ್ಯರೊಂದಿಗೆ ಚಿಕಿತ್ಸಾ ಆಯ್ಕೆಗಳನ್ನು ಚರ್ಚಿಸಿ",
            "rec3": "ನಿಯಮಿತ ಮೇಲ್ವಿಚಾರಣೆ ಅವಶ್ಯಕ",
            "rec4": "ರೋಗಲಕ್ಷಣಗಳು ಹದಗೆಟ್ಟರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ",
            "disclaimer": "ವೈದ್ಯಕೀಯ ಹಕ್ಕು ನಿರಾಕರಣೆ",
            "disclaimer_text": "ಈ ವರದಿಯು ಕೇವಲ ಶೈಕ್ಷಣಿಕ ಉದ್ದೇಶಗಳಿಗಾಗಿ AI ಯಿಂದ ರಚಿಸಲ್ಪಟ್ಟಿದೆ. ರೋಗನಿರ್ಣಯ ಮತ್ತು ಚಿಕಿತ್ಸೆಗಾಗಿ ಯಾವಾಗಲೂ ಅರ್ಹ ನೇತ್ರತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
            "not_specified": "ನಿರ್ದಿಷ್ಟಪಡಿಸಲಾಗಿಲ್ಲ",
            "years": "ವರ್ಷಗಳು",
        },
        "Hindi (India)": {
            "title": "लुमिनापाथ - AI रेटिनल विश्लेषण रिपोर्ट",
            "report_lang": "रिपोर्ट भाषा",
            "report_date": "रिपोर्ट तिथि",
            "patient_details": "रोगी एवं क्लिनिक विवरण",
            "patient_name": "रोगी का नाम",
            "patient_id": "रोगी ID",
            "age": "आयु",
            "gender": "लिंग",
            "email": "ईमेल",
            "physician": "संदर्भित चिकित्सक",
            "diagnosis": "निदान",
            "detected": "पता चली स्थिति",
            "overview": "चिकित्सा अवलोकन",
            "recommendations": "सिफारिशें",
            "rec1": "अपने नेत्र रोग विशेषज्ञ के साथ फॉलो-अप निर्धारित करें",
            "rec2": "अपने चिकित्सक के साथ उपचार विकल्पों पर चर्चा करें",
            "rec3": "नियमित निगरानी आवश्यक है",
            "rec4": "यदि लक्षण बिगड़ें तो अपने डॉक्टर से संपर्क करें",
            "disclaimer": "चिकित्सा अस्वीकरण",
            "disclaimer_text": "यह रिपोर्ट केवल शैक्षिक उद्देश्यों के लिए AI द्वारा उत्पन्न की गई है। निदान और उपचार के लिए हमेशा योग्य नेत्र रोग विशेषज्ञ से परामर्श लें।",
            "not_specified": "निर्दिष्ट नहीं",
            "years": "वर्ष",
        },
        "Tamil": {
            "title": "லுமினாபாத் - AI விழித்திரை பகுப்பாய்வு அறிக்கை",
            "report_lang": "அறிக்கை மொழி",
            "report_date": "அறிக்கை தேதி",
            "patient_details": "நோயாளி மற்றும் மருத்துவமனை விவரங்கள்",
            "patient_name": "நோயாளியின் பெயர்",
            "patient_id": "நோயாளி ID",
            "age": "வயது",
            "gender": "பாலினம்",
            "email": "மின்னஞ்சல்",
            "physician": "பரிந்துரைத்த மருத்துவர்",
            "diagnosis": "நோய் கண்டறிதல்",
            "detected": "கண்டறியப்பட்ட நிலை",
            "overview": "மருத்துவ கண்ணோட்டம்",
            "recommendations": "பரிந்துரைகள்",
            "rec1": "உங்கள் கண் மருத்துவரிடம் தொடர் சந்திப்பு திட்டமிடுங்கள்",
            "rec2": "உங்கள் மருத்துவரிடம் சிகிச்சை விருப்பங்களை விவாதியுங்கள்",
            "rec3": "தொடர் கண்காணிப்பு அவசியம்",
            "rec4": "அறிகுறிகள் மோசமாகினால் உங்கள் மருத்துவரை தொடர்பு கொள்ளுங்கள்",
            "disclaimer": "மருத்துவ மறுப்பு",
            "disclaimer_text": "இந்த அறிக்கை கல்வி நோக்கங்களுக்காக மட்டுமே AI ஆல் உருவாக்கப்பட்டது. நோய் கண்டறிதல் மற்றும் சிகிச்சைக்கு எப்போதும் தகுதிவாய்ந்த கண் மருத்துவரை அணுகுங்கள்.",
            "not_specified": "குறிப்பிடப்படவில்லை",
            "years": "ஆண்டுகள்",
        },
        "Telugu": {
            "title": "లుమినాపాత్ - AI రెటినల్ విశ్లేషణ నివేదిక",
            "report_lang": "నివేదిక భాష",
            "report_date": "నివేదిక తేదీ",
            "patient_details": "రోగి మరియు క్లినిక్ వివరాలు",
            "patient_name": "రోగి పేరు",
            "patient_id": "రోగి ID",
            "age": "వయసు",
            "gender": "లింగం",
            "email": "ఇమెయిల్",
            "physician": "సూచించిన వైద్యుడు",
            "diagnosis": "రోగనిర్ధారణ",
            "detected": "గుర్తించిన పరిస్థితి",
            "overview": "వైద్య అవలోకనం",
            "recommendations": "సిఫారసులు",
            "rec1": "మీ నేత్ర వైద్యునితో ఫాలో-అప్ నిర్ణయించుకోండి",
            "rec2": "మీ వైద్యునితో చికిత్స ఎంపికలను చర్చించండి",
            "rec3": "నిరంతర పర్యవేక్షణ అవసరం",
            "rec4": "లక్షణాలు తీవ్రమైతే వైద్యుడిని సంప్రదించండి",
            "disclaimer": "వైద్య నిరాకరణ",
            "disclaimer_text": "ఈ నివేదిక కేవలం విద్యా ప్రయోజనాల కోసం AI చే రూపొందించబడింది. రోగనిర్ధారణ మరియు చికిత్స కోసం అర్హత గల నేత్ర వైద్యుని సంప్రదించండి.",
            "not_specified": "పేర్కొనబడలేదు",
            "years": "సంవత్సరాలు",
        },
    }

    # Get translated labels, or fall back to English
    t = translations.get(language, {
        "title": "LuminaPath - AI Retinal Analysis Report",
        "report_lang": "Report Language",
        "report_date": "Report Date",
        "patient_details": "Patient & Clinic Details",
        "patient_name": "Patient Name",
        "patient_id": "Patient ID",
        "age": "Age",
        "gender": "Gender",
        "email": "Email",
        "physician": "Referring Physician",
        "diagnosis": "Diagnosis",
        "detected": "Detected Condition",
        "overview": "Medical Overview",
        "recommendations": "Recommendations",
        "rec1": "Schedule a follow-up with your ophthalmologist",
        "rec2": "Discuss treatment options with your physician",
        "rec3": "Regular monitoring is essential",
        "rec4": "Contact your doctor if symptoms worsen",
        "disclaimer": "Medical Disclaimer",
        "disclaimer_text": "This report is AI-generated for educational purposes only. Always consult a qualified ophthalmologist for diagnosis and treatment.",
        "not_specified": "Not specified",
        "years": "years",
    })

    return f"""👁️ {t['title']}
{t['report_lang']}: {language}
{t['report_date']}: {report_date} | {report_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 {t['patient_details']}

{t['patient_name']}:     {patient_name}
{t['patient_id']}:       {patient_id}
{t['age']}:              {patient_age} {t['years']}
{t['gender']}:           {gender}
{t['email']}:            {email}
{t['physician']}:        {physician if physician else t['not_specified']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 {t['diagnosis']}

{t['detected']}: {disease_display}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 {t['overview']}

{explanation_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 {t['recommendations']}

• {t['rec1']}
• {t['rec2']}
• {t['rec3']}
• {t['rec4']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ {t['disclaimer']}

{t['disclaimer_text']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LuminaPath AI System | {report_date} | {report_time}
"""