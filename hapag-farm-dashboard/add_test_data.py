import requests
import json
from datetime import datetime

# Test data
test_data = {
    "2024-01-15T10:00:00": {
        "temperature": 28.5,
        "humidity": 65.2,
        "soil_moisture": 45.8,
        "ph": 6.8,
        "timestamp": "2024-01-15T10:00:00"
    },
    "2024-01-15T11:00:00": {
        "temperature": 29.1,
        "humidity": 63.5,
        "soil_moisture": 44.2,
        "ph": 6.9,
        "timestamp": "2024-01-15T11:00:00"
    }
}

# Add to Firebase
url = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app/sensor_logs.json"

try:
    response = requests.put(url, json=test_data)
    print(f"Status: {response.status_code}")
    print("Test data added to Firebase!")
except Exception as e:
    print(f"Error: {e}")