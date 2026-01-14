# Hapag Farm - Inspect ML Model Files
# View what's inside the .pkl files
# -*- coding: utf-8 -*-

import joblib
import numpy as np
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("HAPAG FARM - MODEL INSPECTION")
print("=" * 60)

# Load the models
print("\n[1] Loading .pkl files...")
model = joblib.load('hapag_crop_model.pkl')
encoder = joblib.load('label_encoder.pkl')
print("✓ Files loaded successfully")

# Model Information
print("\n[2] MODEL INFORMATION")
print("-" * 60)
print(f"Model Type:        {type(model).__name__}")
print(f"Number of Trees:   {model.n_estimators}")
print(f"Input Features:    {model.n_features_in_}")
print(f"Feature Names:     N, P, K, Soil_pH, Humidity")
print(f"Random State:      {model.random_state}")

# Encoder Information
print("\n[3] LABEL ENCODER INFORMATION")
print("-" * 60)
print(f"Total Crop Classes: {len(encoder.classes_)}")
print(f"\nAll Crops ({len(encoder.classes_)}):")
for i, crop in enumerate(encoder.classes_, 1):
    print(f"  {i:2d}. {crop}")

# Feature Importance
print("\n[4] FEATURE IMPORTANCE")
print("-" * 60)
features = ['N', 'P', 'K', 'Soil_pH', 'Humidity']
importances = model.feature_importances_
for feature, importance in zip(features, importances):
    bar = "█" * int(importance * 50)
    print(f"{feature:12s} {importance:.4f} {bar}")

# Test Predictions
print("\n[5] TEST PREDICTIONS")
print("-" * 60)

test_cases = [
    {"name": "High NPK", "values": [150, 40, 180, 6.5, 70]},
    {"name": "Low NPK", "values": [40, 15, 60, 6.0, 65]},
    {"name": "Medium NPK", "values": [80, 25, 100, 6.5, 60]},
]

for test in test_cases:
    prediction = model.predict([test["values"]])[0]
    predicted_crop = encoder.classes_[int(prediction)] if isinstance(prediction, (int, np.integer)) else prediction
    
    # Get confidence if available
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba([test["values"]])[0]
        confidence = np.max(proba) * 100
        print(f"{test['name']:12s} -> {predicted_crop:15s} (Confidence: {confidence:.1f}%)")
    else:
        print(f"{test['name']:12s} -> {predicted_crop}")

# Model Statistics
print("\n[6] MODEL STATISTICS")
print("-" * 60)
print(f"Model Size:        ~25.6 MB")
print(f"Encoder Size:      ~1.6 KB")
print(f"Training Algorithm: Random Forest")
print(f"Trained on:        crop_yield_dataset.csv")

print("\n" + "=" * 60)
print("✓ INSPECTION COMPLETE")
print("=" * 60)
