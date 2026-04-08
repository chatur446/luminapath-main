# LuminaPath - Setup Instructions

## 🚀 Quick Start Guide

### Prerequisites
- Windows OS
- Python 3.8 or higher
- Internet connection

---

## Installation Steps

### 1. Extract the ZIP
Extract to any location, e.g., `C:\Users\YourName\Desktop\`

### 2. Open PowerShell
- Press `Win + X`
- Select "Windows PowerShell" or "Terminal"
- Navigate to project:
```powershell
cd "C:\Users\YourName\Desktop\retinal final project\lumina_path"
```

### 3. Create Virtual Environment
```powershell
python -m venv venv
```

### 4. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

**If you get execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 6. Configure Environment Variables
1. Go to `backend` folder
2. Copy `.env.example` to `.env`
3. Edit `.env` file and add your API keys:
   - Get Gemini API Key from: https://makersuite.google.com/app/apikey
   - Add your Gmail credentials for email reports

### 7. Run the Application

**Terminal 1 - Backend Server:**
```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend Server:**
```powershell
cd frontend
..\venv\Scripts\python.exe -m streamlit run app.py
```

### 8. Access the Application
Open browser: **http://localhost:8501**

---

## Troubleshooting

**Port already in use:**
```powershell
netstat -ano | findstr "8000"
taskkill /PID [process_id] /F
```

**Missing modules:**
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Support
For issues, contact the developer.
