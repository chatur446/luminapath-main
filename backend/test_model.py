import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image
import os

# Load model
print("Loading model...")
model = keras.models.load_model(r'C:\Users\a\Desktop\luminapath-main\model\Retinal_OCT_C8_model.h5', compile=False)
print("Model loaded!")

# Class mapping
CLASS_MAPPING = {
    0: "AMD - Age-related Macular Degeneration",
    1: "CNV - Choroidal Neovascularization",
    2: "CSR - Central Serous Retinopathy",
    3: "DME - Diabetic Macular Edema",
    4: "DR - Diabetic Retinopathy",
    5: "DRUSEN - Yellow deposits under the retina",
    6: "MH - Macular Hole",
    7: "NORMAL - Healthy eyes"
}

def predict_image(image_path):
    print(f"\nAnalyzing: {image_path}")
    
    # Load and preprocess
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img = img.resize((224, 224), Image.BILINEAR)
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    # Predict
    predictions = model.predict(img_array, verbose=0)
    probabilities = predictions[0]
    
    # Results
    predicted_class = np.argmax(probabilities)
    confidence = probabilities[predicted_class] * 100
    
    print("\n" + "="*60)
    print("PREDICTION RESULTS")
    print("="*60)
    print(f"🏆 Predicted: {CLASS_MAPPING[predicted_class]}")
    print(f"📊 Confidence: {confidence:.2f}%")
    print()
    print("All class probabilities:")
    print("-"*60)
    
    # Sort by probability
    sorted_indices = np.argsort(probabilities)[::-1]
    for idx in sorted_indices:
        bar = "█" * int(probabilities[idx] * 50)
        print(f"{CLASS_MAPPING[idx][:40]:<40} {probabilities[idx]*100:6.2f}% {bar}")

# Find any image in static/uploaded_images or ask for path
upload_dir = r'C:\Users\a\Desktop\luminapath-main\static\uploaded_images'
images = [f for f in os.listdir(upload_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

if images:
    # Test on the most recent uploaded image
    image_path = os.path.join(upload_dir, "CNV-1016042-1.jpeg")
    predict_image(image_path)
else:
    print("No images found in static/uploaded_images/")
    print("Please upload an OCT scan through the app first, then run this script again.")