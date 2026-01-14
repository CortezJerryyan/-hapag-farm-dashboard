# Hapag Farm - Sensor Forecasting
import numpy as np
from datetime import datetime, timedelta
import joblib

class SensorForecaster:
    def __init__(self):
        self.history_window = 10  # Use last 10 readings
    
    def forecast(self, historical_data, sensor_name, hours_ahead=24):
        """Simple linear regression forecast"""
        if len(historical_data) < 3:
            return None
        
        values = np.array(historical_data[-self.history_window:])
        x = np.arange(len(values))
        
        # Linear fit
        coeffs = np.polyfit(x, values, 1)
        slope, intercept = coeffs
        
        # Predict future value
        future_x = len(values) + (hours_ahead / 24)
        predicted = slope * future_x + intercept
        change = predicted - values[-1]
        
        # Critical thresholds
        thresholds = {
            'N': (40, 140), 'P': (20, 80), 'K': (40, 200),
            'Soil_pH': (5.5, 7.5), 'Humidity': (40, 80), 'Temperature': (20, 35)
        }
        
        alert = None
        if sensor_name in thresholds:
            low, high = thresholds[sensor_name]
            if predicted < low:
                days = hours_ahead / 24
                alert = f"{sensor_name} will reach critical LOW in {days:.0f} days"
            elif predicted > high:
                days = hours_ahead / 24
                alert = f"{sensor_name} will reach critical HIGH in {days:.0f} days"
        
        return {
            'current': float(values[-1]),
            'predicted': float(predicted),
            'change': float(change),
            'trend': 'increasing' if slope > 0 else 'decreasing',
            'alert': alert
        }

def generate_forecasts(sensor_history):
    """Generate forecasts for all sensors"""
    forecaster = SensorForecaster()
    forecasts = {}
    
    for sensor, readings in sensor_history.items():
        if len(readings) >= 3:
            forecast_24h = forecaster.forecast(readings, sensor, 24)
            forecast_72h = forecaster.forecast(readings, sensor, 72)
            
            forecasts[sensor] = {
                '24h': forecast_24h,
                '72h': forecast_72h
            }
    
    return forecasts
