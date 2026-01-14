# Hapag Farm - ML Model Training Script
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
import joblib

print("=" * 60)
print("HAPAG FARM - ML MODEL TRAINING")
print("=" * 60)

# Step 1: Load Dataset
print("\n[STEP 1] Loading crop_yield_dataset.csv...")
try:
    df = pd.read_csv('crop_yield_dataset.csv')
    print(f"✓ Dataset loaded: {len(df)} rows")
except FileNotFoundError:
    print("✗ Error: crop_yield_dataset.csv not found!")
    print("  Please place your dataset in the same folder as this script.")
    exit(1)

# Step 2: Preprocessing
print("\n[STEP 2] Preprocessing data...")

# Keep only required columns
keep_cols = ['Date', 'N', 'P', 'K', 'Soil_pH', 'Humidity', 'Crop_Type']
df_clean = df[keep_cols].copy()

# Define sensor features (same as Colab)
sensor_features = ['N', 'P', 'K', 'Soil_pH', 'Humidity']

# Handle missing/zero values
df_clean[sensor_features] = df_clean[sensor_features].replace(0, np.nan)
imputer = SimpleImputer(strategy='median')
df_clean[sensor_features] = imputer.fit_transform(df_clean[sensor_features])

print(f"✓ Features: {sensor_features}")
print(f"✓ Missing values handled")

# Step 3: Prepare Training Data
print("\n[STEP 3] Preparing training data...")

X = df_clean[sensor_features]
y = df_clean['Crop_Type']

# Encode crop labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

print(f"✓ Total samples: {len(X)}")
print(f"✓ Crop classes: {len(label_encoder.classes_)}")
print(f"✓ Crops: {', '.join(label_encoder.classes_[:5])}...")

# Split data: 60% Train, 20% Val, 20% Test
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
)

print(f"✓ Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

# Step 4: Train Model
print("\n[STEP 4] Training Random Forest model...")

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Calculate accuracies
train_acc = model.score(X_train, y_train)
val_acc = model.score(X_val, y_val)
test_acc = model.score(X_test, y_test)

print(f"✓ Training Accuracy:   {train_acc:.4f} ({train_acc*100:.2f}%)")
print(f"✓ Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
print(f"✓ Test Accuracy:       {test_acc:.4f} ({test_acc*100:.2f}%)")

# Step 5: Save Models
print("\n[STEP 5] Saving model files...")

joblib.dump(model, 'hapag_crop_model.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')

print("✓ hapag_crop_model.pkl saved")
print("✓ label_encoder.pkl saved")

# Step 6: Verify
print("\n[STEP 6] Verifying saved models...")

loaded_model = joblib.load('hapag_crop_model.pkl')
loaded_encoder = joblib.load('label_encoder.pkl')

# Test prediction
test_input = [[100, 30, 120, 6.5, 65]]  # Sample: N, P, K, pH, Humidity
prediction_idx = loaded_model.predict(test_input)[0]
predicted_crop = loaded_encoder.classes_[prediction_idx]

print(f"✓ Test prediction: {predicted_crop}")
print(f"✓ Model features: {loaded_model.n_features_in_}")
print(f"✓ Encoder classes: {len(loaded_encoder.classes_)}")

print("\n" + "=" * 60)
print("✓ MODEL TRAINING COMPLETE!")
print("=" * 60)
print("\nYour .pkl files are ready to use in the Flask app!")
print("Run: python app.py")
