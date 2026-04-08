"""Loads app settings from .env file"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Grab settings from .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """All app settings in one place"""
    
    # AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Email settings
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "LuminaPath AI System")
    
    # Backup email option
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_SENDER_EMAIL = os.getenv("SENDGRID_SENDER_EMAIL", "noreply@luminapath.com")
    
    # Where the AI model lives
    MODEL_PATH = os.getenv("MODEL_PATH", str(Path(__file__).parent.parent / "model" / "Retinal_OCT_C8_model.h5"))
    
    # Server settings
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # File folders
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_DIR = BASE_DIR / "static" / "uploaded_images"
    REPORTS_DIR = BASE_DIR / "reports" / "pdf_files"
    MODEL_DIR = BASE_DIR / "model"
    
    @classmethod
    def validate(cls):
        """Check if all required settings exist"""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set")
        
        if not cls.GMAIL_USER and not cls.SENDGRID_API_KEY:
            errors.append("Either GMAIL_USER or SENDGRID_API_KEY must be set for email functionality")
        
        if cls.GMAIL_USER and not cls.GMAIL_APP_PASSWORD:
            errors.append("GMAIL_APP_PASSWORD is required when using Gmail SMTP")
        
        if errors:
            raise ValueError(
                "Missing required environment variables:\n" + 
                "\n".join(f"  - {error}" for error in errors) +
                "\n\nPlease check your .env file."
            )
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """Make sure all folders exist"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODEL_DIR.mkdir(parents=True, exist_ok=True)


# Auto-load settings when imported
try:
    Config.validate()
    Config.ensure_directories()
    print("✅ Configuration loaded successfully")
except ValueError as e:
    print(f"⚠️ Configuration Warning: {e}")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
