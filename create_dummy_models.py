import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

print("Creating dummy model files for testing...")

# Create dummy training data (same structure as your Colab)
np.random.seed(42)
n_samples = 1000

# Generate dummy data with same features as your training
dummy_X = np.random.rand(n_samples, 5) * [200, 100, 300, 9, 100]  # N, P, K, pH, Humidity ranges
dummy_X[:, 3] = dummy_X[:, 3] + 4.5  # pH range 4.5-13.5

# Create dummy crop labels (23 crops from your list)
crops = [
    "Sweet Potatoes", "Munggo", "Peanuts", "Sitaw", "Tomatoes", "Lettuce", 
    "Eggplant", "Chili", "Cabbage", "Bell Peppers", "Broccoli", "Corn",
    "Kangkong", "Mustasa", "Garlic", "Radish", "Carrots", "Potatoes",
    "Banana", "Onion", "Okra", "Bokchoy", "Rice"
]

dummy_y = np.random.choice(crops, n_samples)

# Create and train dummy models
print("Training dummy Random Forest model...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(dummy_X, dummy_y)

# Create label encoder
label_encoder = LabelEncoder()
label_encoder.fit(crops)

# Save the models
joblib.dump(rf_model, 'hapag_crop_model.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')

print("Dummy model files created!")
print("Files created:")
print("   - hapag_crop_model.pkl")
print("   - label_encoder.pkl")
print("")
print("Your mobile app will now work with ML predictions!")
print("Run: streamlit run hapag_exact_mobile.py --server.port 8506 --server.address 0.0.0.0")