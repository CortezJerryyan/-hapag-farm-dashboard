import requests
from datetime import datetime

# Your device readings - CHANGE THESE VALUES
device_data = {
    "N": 95,           # Nitrogen reading from your device
    "P": 22,           # Phosphorus reading
    "K": 135,          # Potassium reading  
    "ph": 6.8,         # pH reading
    "humidity": 72,    # Humidity reading
    "temperature": 28.5, # Temperature reading
    "timestamp": datetime.now().isoformat()
}

# Add to Firebase
url = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app/sensor_logs.json"
timestamp_key = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

try:
    # Add new reading with timestamp as key
    response = requests.patch(f"{url}", json={timestamp_key: device_data})
    print(f"✅ Data added! Status: {response.status_code}")
    print(f"📊 Added: N={device_data['N']}, P={device_data['P']}, K={device_data['K']}, pH={device_data['ph']}")
except Exception as e:
    print(f"❌ Error: {e}")