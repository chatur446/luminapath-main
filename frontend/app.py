"""LuminaPath - Main web interface for retinal analysis"""

import streamlit as st
import requests
import os
from pathlib import Path
import time
import json
from datetime import datetime

# Set up the page
st.set_page_config(
    page_title="LuminaPath - Retinal Analysis",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load fancy styling
css_path = Path(__file__).parent / "neumorphic.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Where the API lives
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Patient data storage
PATIENT_HISTORY_FILE = Path(__file__).parent.parent / "patient_history.json"

# Language options (common suggestions)
LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Hindi",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Arabic",
    "Portuguese",
    "Russian",
    "Japanese",
    "Korean",
    "Italian",
    "Dutch",
    "Turkish",
    "Polish",
    "Vietnamese",
    "Thai",
    "Swedish",
    "Greek",
    "Hebrew",
    "Indonesian",
    "Malay",
    "Filipino",
    "Bengali",
    "Urdu",
    "Punjabi",
    "Tamil",
    "Telugu",
    "Marathi",
    "Gujarati",
    "Kannada",
    "Other (Type Below)"
]


def load_patient_history():
    """Get saved patient records"""
    try:
        if PATIENT_HISTORY_FILE.exists():
            with open(PATIENT_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}


def save_patient_history(patient_data):
    """Remember this patient for next time"""
    try:
        history = load_patient_history()
        patient_key = patient_data['patient_id']
        history[patient_key] = {
            'name': patient_data['patient_name'],
            'age': patient_data['patient_age'],
            'gender': patient_data['patient_gender'],
            'email': patient_data['patient_email'],
            'doctor': patient_data.get('doctor_name', ''),
            'last_visit': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Keep only last 50
        if len(history) > 50:
            # Sort by last_visit and keep most recent 50
            sorted_history = dict(sorted(history.items(), 
                                        key=lambda x: x[1].get('last_visit', ''), 
                                        reverse=True)[:50])
            history = sorted_history
        
        with open(PATIENT_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        st.session_state.patient_history = history
    except Exception as e:
        print(f"Error saving patient history: {e}")


def get_patient_suggestions():
    """List of patients for quick-fill"""
    history = st.session_state.patient_history
    suggestions = []
    for patient_id, data in history.items():
        suggestions.append(f"{data['name']} (ID: {patient_id})")
    return sorted(suggestions)


# Remember things while user is here
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'patient_history' not in st.session_state:
    st.session_state.patient_history = load_patient_history()
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'full_report' not in st.session_state:
    st.session_state.full_report = None
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'send_email_clicked' not in st.session_state:
    st.session_state.send_email_clicked = False


def main():
    """Main app - shows the UI"""
    
    # Top of page
    st.markdown("""
        <div class="header">
            <h1>👁️ LuminaPath</h1>
            <p class="subtitle">AI-Powered Retinal Report Generator</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Two-column layout with better balance
    col1, col2 = st.columns([1.1, 1.3])
    
    with col1:
        # Upload area
        st.markdown('<div class="section-header">📸 Upload OCT Scan</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose an OCT scan image",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="Upload a clear OCT scan image for analysis",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.image(uploaded_file, caption="Uploaded OCT Scan", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    with col2:
        # Patient info form
        st.markdown('<div class="section-header">📋 Patient Information</div>', unsafe_allow_html=True)
        
        # Quick-fill from history
        patient_suggestions = get_patient_suggestions()
        if patient_suggestions:
            st.markdown("**Quick Load Previous Patient:**")
            selected = st.selectbox(
                "Select from history",
                options=["-- New Patient --"] + patient_suggestions,
                key="patient_selector",
                label_visibility="collapsed"
            )
            
            # Fill form if patient selected
            if selected != "-- New Patient --":
                # Extract patient ID from selection
                patient_id_match = selected.split("ID: ")[-1].rstrip(")")
                if patient_id_match in st.session_state.patient_history:
                    st.session_state.selected_patient = st.session_state.patient_history[patient_id_match]
            else:
                st.session_state.selected_patient = None
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("patient_form"):
            # Use saved patient data or defaults
            default_name = st.session_state.selected_patient['name'] if st.session_state.selected_patient else ""
            default_age = st.session_state.selected_patient['age'] if st.session_state.selected_patient else 30
            default_gender = st.session_state.selected_patient['gender'] if st.session_state.selected_patient else "Male"
            default_email = st.session_state.selected_patient['email'] if st.session_state.selected_patient else ""
            default_doctor = st.session_state.selected_patient.get('doctor', '') if st.session_state.selected_patient else ""
            
            patient_name = st.text_input(
                "Patient Name *",
                value=default_name,
                placeholder="Enter full name",
                help="Full legal name of the patient"
            )
            
            col_age, col_gender = st.columns(2)
            
            with col_age:
                patient_age = st.number_input(
                    "Age *",
                    min_value=1,
                    max_value=120,
                    value=default_age,
                    help="Patient's age in years"
                )
            
            with col_gender:
                gender_index = ["Male", "Female", "Other"].index(default_gender) if default_gender in ["Male", "Female", "Other"] else 0
                patient_gender = st.radio(
                    "Gender",
                    options=["Male", "Female", "Other"],
                    index=gender_index,
                    help="Patient's gender",
                    horizontal=True
                )
            
            patient_id = st.text_input(
                "Patient ID *",
                value=patient_id_match if st.session_state.selected_patient else "",
                placeholder="e.g., P12345",
                help="Unique patient identifier"
            )
            
            patient_email = st.text_input(
                "Email Address *",
                value=default_email,
                placeholder="patient@example.com",
                help="Email to receive the report"
            )
            
            doctor_name = st.text_input(
                "Referring Physician",
                value=default_doctor,
                placeholder="Dr. Name (optional)",
                help="Name of referring ophthalmologist"
            )
            
            # Language selection with custom input option
            st.markdown("**Report Language ***")
            
            # Top languages with Kannada, Hindi (India), English prioritized
            top_languages = ["Kannada", "Hindi (India)", "English", "Spanish", "French", "German", "Chinese (Simplified)", "Arabic", "Other"]
            language_suggestion = st.radio(
                "Choose language",
                options=top_languages,
                index=2,  # Default to English
                help="Select from common languages",
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # If Other is selected, show text input
            if language_suggestion == "Other":
                custom_language = st.text_input(
                    "Enter your language",
                    placeholder="e.g., Telugu, Tamil, Bengali, Japanese...",
                    help="Type any language"
                )
                final_language = custom_language.strip() if custom_language.strip() else "English"
            else:
                final_language = language_suggestion
            
            # Use final_language variable for backward compatibility
            language = final_language
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Big button
            submit_button = st.form_submit_button(
                "🔬 Generate Medical Report",
                use_container_width=True,
                type="primary"
            )
    
    # When user clicks generate
    if submit_button:
        # Check required fields
        if not st.session_state.uploaded_file:
            st.error("❌ Please upload an OCT scan image")
            return
        
        if not patient_name or not patient_id or not patient_email:
            st.error("❌ Please fill all required fields marked with *")
            return
        
        if '@' not in patient_email:
            st.error("❌ Please enter a valid email address")
            return
        
        # Save patient to history
        save_patient_history({
            'patient_name': patient_name,
            'patient_age': patient_age,
            'patient_gender': patient_gender,
            'patient_id': patient_id,
            'patient_email': patient_email,
            'doctor_name': doctor_name
        })
        
        # Generate report
        generate_report(
            uploaded_file=st.session_state.uploaded_file,
            patient_name=patient_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_id=patient_id,
            patient_email=patient_email,
            doctor_name=doctor_name,
            language=language
        )
    
    # Display report if it exists in session state
    if st.session_state.full_report and st.session_state.report_data:
        st.markdown("---")
        st.markdown("### 📋 Your Complete Medical Report")
        
        # Display report in a styled container
        st.markdown("""
        <style>
        .report-container {
            background-color: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #1a237e;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            color: #000000;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="report-container">{st.session_state.full_report}</div>', unsafe_allow_html=True)
        
        # Action buttons
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📥 Download Report (.txt)",
                data=st.session_state.full_report,
                file_name=f"LuminaPath_Report_{st.session_state.report_data['patient_name']}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_txt_main"
            )
        
        with col2:
            if st.button("📋 Copy Report", use_container_width=True, key="copy_report_main"):
                st.success("✅ Report copied to clipboard!")
        
        with col3:
            if st.button("📧 Send to Email", use_container_width=True, type="primary", key="send_email_main"):
                st.session_state.send_email_clicked = True
                st.rerun()
    
    # Handle email sending outside button callback
    if st.session_state.send_email_clicked and st.session_state.report_data:
        with st.spinner("Sending report via email..."):
            email_payload = st.session_state.report_data.copy()
            email_payload["recipient_email"] = email_payload["email"]
            email_payload["method"] = "gmail"
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/send-report", 
                    json=email_payload,
                    timeout=20
                )
                
                if response.status_code == 200:
                    st.success(f"✅ Report sent to {email_payload['email']}!")
                else:
                    st.error(f"❌ Email failed: {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Email timeout. Please try again.")
            except Exception as e:
                st.error(f"❌ Email error: {str(e)}")
        
        # Reset flag after sending
        st.session_state.send_email_clicked = False
    
    # Bottom of page
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: #888; font-size: 0.9em; padding: 20px;">
            <p>LuminaPath - AI-Powered Retinal Analysis System</p>
            <p style="font-size: 0.8em;">This system uses advanced AI for medical insights. Always consult a qualified ophthalmologist.</p>
        </div>
    """, unsafe_allow_html=True)


def display_report_preview(patient_name, patient_age, patient_gender, patient_id, 
                          patient_email, doctor_name, predicted_disease, explanation_text, pdf_path, oct_image):
    """Show nice report preview before download"""
    
    # Get time info once
    now = datetime.now()
    report_date = now.strftime("%B %d, %Y")
    report_time = now.strftime("%I:%M %p")
    report_datetime = now.strftime("%B %d, %Y at %I:%M %p")
    report_id = f"LP-{now.strftime('%Y%m%d%H%M%S')}"
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Professional Header
    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin-bottom: 8px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">👁️ LuminaPath</h1>
        <p style="color: #f0f0f0; font-style: italic; font-size: 1.2em; margin-bottom: 5px;">AI-Powered Retinal Analysis Report</p>
        <p style="color: #e0e0e0; font-size: 0.95em;">Generated on {report_datetime}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Report Metadata
    col_meta1, col_meta2 = st.columns(2)
    
    with col_meta1:
        st.markdown(f"""
        <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #667eea;">
            <p style="margin: 5px 0; color: #333;"><b>📅 Report Date:</b> {report_date}</p>
            <p style="margin: 5px 0; color: #333;"><b>🆔 Report ID:</b> {report_id}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_meta2:
        st.markdown(f"""
        <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #764ba2;">
            <p style="margin: 5px 0; color: #333;"><b>🕐 Report Time:</b> {report_time}</p>
            <p style="margin: 5px 0; color: #333;"><b>🌍 Language:</b> English</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Patient and Clinic Details Section
    st.markdown("""
    <div style="background: #1a237e; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: white;">👤 Patient and Clinic Details</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for patient details
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #e0e0e0; height: 100%;">
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Patient Name:</b><br/><span style="font-size: 1.1em;">{patient_name}</span></p>
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Patient ID:</b><br/>{patient_id}</p>
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Age:</b><br/>{patient_age} years</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_p2:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #e0e0e0; height: 100%;">
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Gender:</b><br/>{patient_gender}</p>
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Referring Physician:</b><br/>{doctor_name if doctor_name else 'Not Specified'}</p>
            <p style="margin: 10px 0; color: #000;"><b style="color: #1a237e;">Email:</b><br/>{patient_email}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Diagnosis Section
    st.markdown("""
    <div style="background: #c62828; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: white;">🔬 Diagnosis</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: #ffebee; padding: 25px; border-radius: 10px; border: 2px solid #c62828;">
        <p style="margin: 10px 0; color: #000;"><b style="color: #c62828; font-size: 1.1em;">Predicted Disease:</b></p>
        <p style="margin: 5px 0; color: #c62828; font-size: 1.3em; font-weight: bold;">{predicted_disease}</p>
        <p style="margin: 15px 0 5px 0; color: #000;"><b style="color: #1a237e;">Explanation Type:</b> Educational Overview</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # OCT Scan Image Section
    if oct_image:
        st.markdown("""
        <div style="background: #283593; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin: 0; color: white;">📸 OCT Scan Image</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col_img1, col_img2, col_img3 = st.columns([0.5, 3, 0.5])
        with col_img2:
            st.image(oct_image, caption="Retinal OCT Scan", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Educational Overview Section
    st.markdown("""
    <div style="background: #2e7d32; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: white;">📚 Educational Overview</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Process explanation text to display properly
    if explanation_text and explanation_text.strip():
        st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 10px; border: 2px solid #e0e0e0; color: #000;">
        """, unsafe_allow_html=True)
        
        # Split into lines for better formatting
        lines = explanation_text.split('\n')
        formatted_text = ""
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('['):
                continue
            
            # Check if section header
            if line.endswith(':') and len(line) < 60:
                formatted_text += f"\n**{line}**\n\n"
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                formatted_text += f"{line}\n\n"
            else:
                formatted_text += f"{line}\n\n"
        
        st.markdown(formatted_text)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("📝 Detailed medical analysis will be included in the PDF report.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recommendations Section
    st.markdown("""
    <div style="background: #f57c00; color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: white;">💡 Recommendations</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: white; padding: 25px; border-radius: 10px; border: 2px solid #e0e0e0; color: #000;">
        <p style="margin-bottom: 15px; color: #000;">Based on the AI analysis of the OCT scan, we recommend:</p>
        <ul style="line-height: 1.8; color: #000;">
            <li>Follow-up consultation with a qualified ophthalmologist for clinical correlation</li>
            <li>Additional diagnostic tests if recommended by your physician</li>
            <li>Regular monitoring and adherence to prescribed treatment plans</li>
            <li>Immediate medical attention if symptoms worsen or new symptoms develop</li>
        </ul>
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #f57c00; margin-top: 20px;">
            <p style="margin: 0; color: #c62828; font-weight: bold;">⚠️ Important Notice:</p>
            <p style="margin: 10px 0 0 0; color: #000; font-size: 0.95em;">
                This AI-generated report is for educational and informational purposes only. 
                It should not replace professional medical diagnosis or treatment. Always consult with a 
                qualified healthcare provider for proper medical advice.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Physician Signature Section
    st.markdown(f"""
    <div style="background: white; padding: 25px; border-radius: 10px; border: 2px solid #e0e0e0; margin-top: 30px;">
        <div style="display: flex; justify-content: space-around; margin-top: 40px;">
            <div style="text-align: center; flex: 1;">
                <div style="border-bottom: 2px solid #000; width: 200px; margin: 0 auto 10px auto;"></div>
                <p style="margin: 0; color: #000; font-weight: bold;">{doctor_name if doctor_name else 'Physician Signature'}</p>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">Referring Physician</p>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="border-bottom: 2px solid #000; width: 200px; margin: 0 auto 10px auto;"></div>
                <p style="margin: 0; color: #000; font-weight: bold;">Date: {report_date}</p>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">Report Date</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Download section at the end
    st.markdown("""
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 10px 15px; 
                border-radius: 8px; margin: 20px 0 15px 0; text-align: center;">
        <h3 style="margin: 0; color: white;">📥 Download Complete Report</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="📄 Download Professional PDF Report",
                    data=pdf_bytes,
                    file_name=f"LuminaPath_Report_{patient_id}_{now.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            
            st.success("✅ Report generated successfully!")
            st.info("✉️ A copy has been sent to: " + patient_email)
            
            # Footer
            st.markdown("""
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 10px;">
                <p style="margin: 0; color: #666; font-style: italic; font-size: 0.9em;">
                    This report was generated by LuminaPath AI-Powered Retinal Analysis System.<br/>
                    For clinical interpretation and treatment decisions, please consult with a qualified ophthalmologist.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ PDF file not found. Please regenerate the report.")
    
    st.markdown("<br>", unsafe_allow_html=True)


def generate_report(uploaded_file, patient_name, patient_age, patient_gender, 
                   patient_id, patient_email, doctor_name, language):
    """Talk to backend to make the report"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Analyze the scan
        status_text.text("🔍 Analyzing OCT scan...")
        progress_bar.progress(20)
        
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        # Don't wait forever
        try:
            response = requests.post(
                f"{API_BASE_URL}/predict", 
                files=files, 
                timeout=15  # 15-second timeout
            )
        except requests.exceptions.Timeout:
            status_text.empty()
            progress_bar.empty()
            st.error("⏱️ Prediction timeout: The server took too long to respond. Please try again.")
            return
        except requests.exceptions.ConnectionError:
            status_text.empty()
            progress_bar.empty()
            st.error("🔌 Connection error: Cannot reach the backend server. Please ensure it's running on port 8000.")
            return
        
        if response.status_code != 200:
            status_text.empty()
            progress_bar.empty()
            st.error(f"❌ Prediction failed: {response.text}")
            return
        
        prediction_data = response.json()
        predicted_class = prediction_data.get("predicted_class")
        
        if not predicted_class:
            status_text.empty()
            progress_bar.empty()
            st.error(f"❌ No prediction returned from server")
            return
        
        # Step 2: Get AI explanation
        status_text.text("🤖 Generating medical explanation...")
        progress_bar.progress(40)
        
        explain_payload = {
            "disease_name": predicted_class,
            "language": language
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/explain", 
                json=explain_payload,
                timeout=30  # 30-second timeout for AI explanation
            )
        except requests.exceptions.Timeout:
            status_text.empty()
            progress_bar.empty()
            st.error("⏱️ AI explanation timeout: The AI took too long to respond. Using fallback.")
            explanation_text = "Detailed medical explanation is currently unavailable. Please consult with your ophthalmologist for a comprehensive analysis."
        except Exception as e:
            status_text.empty()
            progress_bar.empty()
            st.warning(f"⚠️ Explanation generation issue: {str(e)}. Using fallback.")
            explanation_text = "Detailed medical explanation is currently unavailable. Please consult with your ophthalmologist for a comprehensive analysis."
        else:
            if response.status_code != 200:
                st.warning(f"⚠️ Explanation generation failed: {response.text}. Using fallback.")
                explanation_text = "Detailed medical explanation is currently unavailable. Please consult with your ophthalmologist for a comprehensive analysis."
            else:
                explanation_data = response.json()
                explanation_text = explanation_data.get("explanation", "")
                
                # Remove debug stuff from AI output
                if "[INFO]" in explanation_text or "[DEBUG]" in explanation_text or "[WARN]" in explanation_text:
                    # Extract only the actual explanation content
                    lines = explanation_text.split('\n')
                    lines = [line for line in lines if not line.strip().startswith('[')]
                    explanation_text = '\n'.join(lines).strip()
        
        # Step 3: Generate Full Medical Report using Gemini
        status_text.text("📄 Generating complete medical report...")
        progress_bar.progress(65)
        
        # Package all patient info
        report_data = {
            "patient_name": patient_name,
            "patient_age": str(patient_age),
            "patient_id": patient_id,
            "explanation": explanation_text,
            "predicted_disease": predicted_class,
            "gender": patient_gender,
            "physician": doctor_name if doctor_name else "",
            "email": patient_email,
            "language": language
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/generate-full-report",
                json=report_data,
                timeout=30  # Longer timeout for Gemini
            )
        except requests.exceptions.Timeout:
            status_text.empty()
            progress_bar.empty()
            st.error("⏱️ Report generation timeout. Please try again.")
            return
        
        if response.status_code != 200:
            status_text.empty()
            progress_bar.empty()
            st.error(f"❌ Report generation failed: {response.text}")
            return
        
        report_response = response.json()
        full_report = report_response.get("report")
        st.session_state.full_report = full_report
        st.session_state.report_data = report_data  # Save for email
        
        # Done!
        status_text.text("✅ Report generation complete!")
        progress_bar.progress(100)
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        st.session_state.report_generated = True
        
        # Success message
        st.success("✅ Medical report generated successfully! Scroll down to view.")
        
    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        status_text.empty()
        st.error("❌ Cannot connect to backend server. Please ensure FastAPI is running on " + API_BASE_URL)
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ An error occurred: {str(e)}")
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")
    finally:
        # Always clean up
        progress_bar.empty()
        status_text.empty()


if __name__ == "__main__":
    main()
