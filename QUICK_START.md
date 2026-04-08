# 🚀 LuminaPath - Quick Setup

## ⚡ Get Running in 5 Minutes

### Step 1: Install Everything
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
pip install streamlit requests
```

### Step 2: Add Your Keys
```bash
# Copy example file
cp .env.example .env

# Edit .env with:
# - GEMINI_API_KEY (get free at https://makersuite.google.com/app/apikey)
# - GMAIL_USER (your email)
# - GMAIL_APP_PASSWORD (from Google Account settings)
```

### Step 3: Drop in the Model File
```bash
# Put Retinal_OCT_C8_model.h5 here:
lumina_path/model/Retinal_OCT_C8_model.h5
```

### Step 4: Start Backend
```bash
cd backend
uvicorn main:app --reload
```
Backend runs at: http://localhost:8000

### Step 5: Start Frontend (New Terminal)
```bash
cd frontend
streamlit run app.py
```
Frontend runs at: http://localhost:8501

---

## 🎯 How to Use It

1. **Upload** OCT scan image
2. **Fill** patient details (name, age, email)
3. **Select** report language
4. **Click** "Generate Medical Report"
5. **Download** PDF + receive email automatically

---

## 🔑 Where to Get Keys

### Gemini API Key
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy key to `.env` as `GEMINI_API_KEY`

### Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate password for "Mail"
5. Copy 16-digit code to `.env` as `GMAIL_APP_PASSWORD`

---

## 🐛 If Something Breaks

**Backend won't start:**
```bash
pip install --upgrade -r backend/requirements.txt
```

**Email not sending:**
- Check Gmail App Password (16 digits, no spaces)
- Turn on 2-Step Verification in Gmail

**Model not found:**
- Make sure `Retinal_OCT_C8_model.h5` is in `lumina_path/model/`

**Frontend can't connect:**
- Check backend is running on port 8000
- Visit http://localhost:8000/docs to verify

---

## 📚 Need More Help?

Check out `README.md` for the complete guide.

---

**Need Help?** Check `PROJECT_COMPLETION_CHECKLIST.md` for detailed verification.
