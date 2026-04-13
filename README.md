# 👁️ LuminaPath

### AI-Powered Retinal Analysis & Report Generatort Generator

LuminaPath analyzes retinal scans using AI and creates professional medical reports with easy-to-understand explanations.

---

## ✨ What It Does

- 🔬 **Scan Analysis** - Automatically detects eye diseases from OCT scans
- 🤖 **AI Explanations** - Plain-English medical insights powered by Google Gemini
- 🎨 **Modern UI** - Clean, easy-to-use interface with 3D effects
- 📄 **Pro PDFs** - Medical-grade reports with patient details
- ✉️ **Auto Email** - Reports sent directly to patient's inbox
- 🌍 **8+ Languages** - English, Spanish, Hindi, Chinese, and more
- 🔒 **Privacy First** - No technical jargon or scary numbers shown to patients

---

## 🛠️ Built With

### Backend
- **Framework**: FastAPI
- **ML/AI**: TensorFlow 2.x, Keras
- **AI API**: Google Gemini 1.5 Flash
- **PDF Generation**: ReportLab
- **Email**: SMTP (Gmail) / SendGrid API

### Frontend
- **Framework**: Streamlit
- **Styling**: Custom Neumorphic CSS
- **UI Components**: Native Streamlit widgets

### Model
- **Architecture**: Custom CNN (8-class classification)
- **Input**: OCT scan images (224x224 RGB)
- **Output**: Retinal condition classification

---

## 📁 Project Structure

```
lumina_path/
│
├── backend/
│   ├── main.py              # FastAPI application & endpoints
│   ├── model_loader.py      # TensorFlow model loading & preprocessing
│   ├── explain.py           # Gemini API integration
│   ├── pdf_generator.py     # PDF report creation
│   ├── email_sender.py      # Email delivery service
│   └── requirements.txt     # Backend dependencies
│
├── frontend/
│   ├── app.py               # Streamlit application
│   └── neumorphic.css       # Custom neumorphic styling
│
├── model/
│   └── Retinal_OCT_C8_model.h5   # Trained Keras model
│
├── static/
│   └── uploaded_images/     # Temporary OCT scan storage
│
├── reports/
│   └── pdf_files/           # Generated PDF reports
│
└── README.md                # Project documentation
```

---

## 🔌 How The API Works

### Backend Endpoints (FastAPI)

#### 1. **POST `/predict`**
Analyze a scan and find out what's wrong.

**Request:**
- `file`: OCT scan image (multipart/form-data)

**Response:**
```json
{
  "predicted_class": "CNV"
}
```

#### 2. **POST `/explain`**
Get a plain-English explanation from AI.

**Request:**
```json
{
  "disease_name": "CNV",
  "language": "English"
}
```

**Response:**
```json
{
  "disease": "CNV",
  "explanation": "Choroidal Neovascularization (CNV) is...",
  "language": "English"
}
```

#### 3. **POST `/generate-pdf`**
Make a professional medical report.

**Request:**
- `file`: OCT scan image
- `patient_name`: Patient's full name
- `patient_age`: Patient's age
- `patient_id`: Unique identifier
- `explanation`: Medical explanation text

**Response:**
```json
{
  "pdf_path": "/path/to/report.pdf",
  "success": true
}
```

#### 4. **POST `/send-report`**
Email the PDF to the patient.

**Request:**
```json
{
  "recipient_email": "patient@example.com",
  "pdf_path": "/path/to/report.pdf",
  "patient_name": "John Doe",
  "method": "gmail"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report sent successfully"
}
```

#### 5. **GET `/`**
Check if the server is alive.

---

## 🎯 What We Can Detect

The AI recognizes 8 retinal conditions:

1. **CNV** - Choroidal Neovascularization
2. **DME** - Diabetic Macular Edema
3. **DRUSEN** - Drusen deposits
4. **NORMAL** - Healthy retina
5. **AMD** - Age-related Macular Degeneration
6. **MH** - Macular Hole
7. **CSR** - Central Serous Retinopathy
8. **DR** - Diabetic Retinopathy

---

## 🚀 How to Set It Up

### What You Need

- Python 3.8 or newer
- pip (comes with Python)
- A Gemini API key ([free here](https://makersuite.google.com/app/apikey))
- Gmail account (for sending reports)

### Setup Steps

#### 1. Get the Code
```bash
git clone https://github.com/chatur466/luminapath-main.git
cd lumina_path
```

#### 2. Install Backend Stuff
```bash
cd backend
pip install -r requirements.txt
```

**Backend `requirements.txt`:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
tensorflow==2.15.0
pillow==10.1.0
numpy==1.24.3
google-generativeai==0.3.1
reportlab==4.0.7
python-dotenv==1.0.0
```

#### 3. Install Frontend Stuff
```bash
cd ../frontend
pip install streamlit==1.28.2 requests==2.31.0
```

#### 4. Add Model File
Place `Retinal_OCT_C8_model.h5` in the `model/` directory.

#### 5. Add Your API Keys

Create a `.env` file in the `backend/` folder:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail SMTP Configuration
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_digit_app_password

# Optional: SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_SENDER_EMAIL=noreply@yourdomain.com
```

---

## 🔧 Getting a Gmail Password for the App App

1. Go to your [Google Account](https://myaccount.google.com/)
2. Click **Security** → turn on **2-Step Verification** (if not already on)
3. Find **App Passwords**
4. Choose **Mail** and **Other**
5. Name it "LuminaPath" → click **Generate**
6. Copy the 16-digit code (ignore spaces)
7. Paste into `.env` as `GMAIL_APP_PASSWORD`

---

## ▶️ Starting the App

### 1. Start Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: `http://localhost:8000`

API docs available at: `http://localhost:8000/docs`

### 2. Start Frontend (Streamlit)

Open a new terminal:

```bash
cd frontend
streamlit run app.py
```

Frontend will run at: `http://localhost:8501`

---

## 📸 Screenshots

Below are some preview screenshots showcasing LuminaPath's interface and report design.

---

## 🏠 Home Screen (Header Section)

<img src="https://github.com/Manishkumarsingh41/luminapath/blob/main/static/uploaded_images/WhatsApp%20Image%202025-11-23%20at%2020.47.36_127d3612.jpg" alt="Home Screen" width="750"/>

---

## 🔍 Analysis Screen (Middle Section)

<img src="https://github.com/Manishkumarsingh41/luminapath/blob/main/static/uploaded_images/WhatsApp%20Image%202025-11-23%20at%2020.47.52_1b2b9938.jpg" alt="Analysis Screen" width="750"/>

---

## 🧾 Generated Report (Bottom Section)

<img src="https://github.com/Manishkumarsingh41/luminapath/blob/main/static/uploaded_images/WhatsApp%20Image%202025-11-23%20at%2020.48.20_5cc0a3e6.jpg" alt="Generated Report" width="750"/>

---

---

## 🎨 Neumorphic Design

LuminaPath features a custom neumorphic (soft UI) design with:

- **Soft shadows** for depth perception
- **Extruded cards** for elevated elements
- **Inset inputs** for interactive fields
- **Smooth animations** for better UX
- **Responsive design** for all screen sizes

Color palette:
- Background: `#e0e0e0`
- Primary: `#1a237e` (Deep Blue)
- Accent: `#283593` (Blue)
- Light Shadow: `rgba(255, 255, 255, 0.8)`
- Dark Shadow: `rgba(184, 185, 190, 0.6)`

---

## 🔄 How It Works (Behind the Scenes)

1. **Patient uploads OCT scan** via Streamlit interface
2. **Fills patient details** (name, age, email, language preference)
3. **Clicks "Generate Report"** button
4. **Backend processes**:
   - Image uploaded to `static/uploaded_images/`
   - Model predicts retinal condition
   - Gemini API generates medical explanation
   - PDF report created with all details
   - Email sent to patient automatically
5. **Patient receives**:
   - Email with PDF attachment
   - Download link in UI

---

## 🧪 Testing

### Test Prediction Endpoint
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@sample_oct.jpg"
```

### Test Explanation Endpoint
```bash
curl -X POST "http://localhost:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{"disease_name": "CNV", "language": "English"}'
```

---

## 🐛 Common Issues

### Backend won't start
- Make sure everything's installed: `pip install -r requirements.txt`
- Check the model file is in the `model/` folder
- Check Python version: `python --version` (needs 3.8 or newer)

### Email not working
- Double-check your Gmail App Password (16 digits, no spaces)
- Make sure 2-Step Verification is turned on
- Check `GMAIL_USER` and `GMAIL_APP_PASSWORD` in `.env`

### Gemini AI not working
- Make sure your API key is valid at [Google AI Studio](https://makersuite.google.com/)
- Check `GEMINI_API_KEY` in `.env`
- You might be out of free API quota

### Frontend can't talk to backend
- Make sure backend is running on port 8000
- Check `API_BASE_URL` in `frontend/app.py`
- Check your firewall isn't blocking it

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Credits

**Developed by:**(https://github.com/Manishkumarsingh41)

**Technologies Used:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Interactive UI framework
- [TensorFlow](https://www.tensorflow.org/) - Deep learning platform
- [Google Gemini](https://ai.google.dev/) - Generative AI API
- [ReportLab](https://www.reportlab.com/) - PDF generation library

**Special Thanks:**
- Medical professionals for domain expertise
- Open-source community for amazing tools
- OCT dataset providers for training data

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📧 Contact

For questions or support, please contact: [singhmanishofficial102@gmail.com]

---

## ⚠️ Medical Disclaimer

LuminaPath is an AI-assisted diagnostic tool designed to aid medical professionals. **This system should not be used as the sole basis for medical diagnosis or treatment decisions.** Always consult with a qualified ophthalmologist or healthcare provider for professional medical advice, diagnosis, and treatment.

---

<div align="center">

**Made with ❤️ for better retinal health**

⭐ Star this repo if you found it helpful!

</div>
