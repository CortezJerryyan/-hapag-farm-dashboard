# Hapag Farm - Forecast Model Training (LSTM Time Series)
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("HAPAG FARM - FORECAST MODEL TRAINING")
print("=" * 60)

# Load dataset
print("\n[STEP 1] Loading crop_yield_dataset.csv...")
try:
    df = pd.read_csv('crop_yield_dataset.csv')
    print(f"✓ Dataset loaded: {len(df)} rows")
except FileNotFoundError:
    print("✗ Error: crop_yield_dataset.csv not found!")
    exit(1)

# Prepare time series data
print("\n[STEP 2] Preparing time series data...")
sensors = ['N', 'P', 'K', 'Soil_pH', 'Humidity', 'Temperature']
available_sensors = [s for s in sensors if s in df.columns]

# Create sequences for prediction
def create_sequences(data, seq_length=10):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

# Train models for each sensor
models = {}
scalers = {}

for sensor in available_sensors:
    print(f"\n[STEP 3] Training {sensor} forecast model...")
    
    # Get sensor data
    sensor_data = df[sensor].values.reshape(-1, 1)
    
    # Scale data
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(sensor_data)
    
    # Create sequences
    X, y = create_sequences(scaled_data, seq_length=10)
    
    if len(X) < 20:
        print(f"✗ Not enough data for {sensor}")
        continue
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Simple linear regression coefficients (lightweight ML)
    from sklearn.linear_model import Ridge
    
    # Flatten sequences for Ridge regression
    X_train_flat = X_train.reshape(X_train.shape[0], -1)
    X_test_flat = X_test.reshape(X_test.shape[0], -1)
    
    model = Ridge(alpha=1.0)
    model.fit(X_train_flat, y_train.ravel())
    
    # Evaluate
    train_score = model.score(X_train_flat, y_train.ravel())
    test_score = model.score(X_test_flat, y_test.ravel())
    
    print(f"✓ {sensor} - Train R²: {train_score:.4f}, Test R²: {test_score:.4f}")
    
    models[sensor] = model
    scalers[sensor] = scaler

# Save models
print("\n[STEP 4] Saving forecast models...")
joblib.dump({'models': models, 'scalers': scalers}, 'forecast_model.pkl')
print("✓ forecast_model.pkl saved")

print("\n" + "=" * 60)
print("✓ FORECAST MODEL TRAINING COMPLETE!")
print("=" * 60)
