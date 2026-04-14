import tensorflow as tf
from tensorflow import keras
import numpy as np

model = keras.models.load_model(r'C:\Users\a\Desktop\luminapath-main\model\Retinal_OCT_C8_model.h5', compile=False)

print('='*60)
print('MODEL SUMMARY')
print('='*60)
model.summary()

print()
print('='*60)
print('BASIC INFO')
print('='*60)
print(f'Total layers: {len(model.layers)}')
print(f'Total parameters: {model.count_params():,}')
print(f'Input shape: {model.input_shape}')
print(f'Output shape: {model.output_shape}')

print()
print('='*60)
print('LAYER DETAILS')
print('='*60)
for i, layer in enumerate(model.layers):
    print(f'Layer {i+1}: {layer.name} | Type: {type(layer).__name__} | Output: {layer.output_shape}')