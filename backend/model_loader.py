"""Loads the AI model and prepares images for analysis"""

import os
import numpy as np
from tensorflow import keras
from PIL import Image
from pathlib import Path

from config import Config

# Model stored here after first load
_model = None
MODEL_PATH = Path(Config.MODEL_PATH).resolve()

# What the model's numbers actually mean
CLASS_MAPPING = {
    "Class_1": "AMD - Age-related Macular Degeneration",
    "Class_2": "CNV - Choroidal Neovascularization",
    "Class_3": "CSR - Central Serous Retinopathy",
    "Class_4": "DME - Diabetic Macular Edema",
    "Class_5": "DR - Diabetic Retinopathy",
    "Class_6": "DRUSEN - Yellow deposits under the retina",
    "Class_7": "MH - Macular Hole",
    "Class_8": "NORMAL - Healthy eyes with no abnormalities"
}


def load_model():
    """Load the AI model (only once, then reuse)"""
    global _model
    
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        print(f"⏳ Loading model from {MODEL_PATH}...")
        # Load without compiling (faster)
        _model = keras.models.load_model(MODEL_PATH, compile=False)
        
        # Warm up for faster first use
        dummy_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
        _ = _model.predict(dummy_input, verbose=0)
        
        print(f"✅ Model loaded and warmed up successfully")
    
    return _model


def preprocess_image(image_file):
    """Get image ready for the AI model"""
    # Open image
    img = Image.open(image_file)
    
    # Make sure it's RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize to what model expects
    target_size = (224, 224)
    img = img.resize(target_size, Image.BILINEAR)
    
    # Turn into numbers (0-1 range)
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # Add batch dimension (required by model)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


def get_model_info():
    """Get model details"""
    model = load_model()
    
    return {
        'input_shape': model.input_shape,
        'output_shape': model.output_shape,
        'total_params': model.count_params(),
        'model_path': MODEL_PATH
    }


def get_disease_name(class_label):
    """Turn model output into readable disease name"""
    return CLASS_MAPPING.get(class_label, class_label)
