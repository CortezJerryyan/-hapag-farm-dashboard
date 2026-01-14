# Hapag Farm - Sensor Forecasting
import numpy as np
from datetime import datetime, timedelta
import joblib
import os

class SensorForecaster:
    def __init__(self):
        self.history_window = 10
        self.models = None
        self.scalers = None
        self.load_models()
    
    def load_models(self):
        """Load trained ML models if available"""
        try:
            if os.path.exists('forecast_model.pkl'):
                data = joblib.load('forecast_model.pkl')
                self.models = data['models']
                self.scalers = data['scalers']
        except:
            pass
    
    def forecast(self, historical_data, sensor_name, hours_ahead=24):
        """ML-based forecast if model exists, else linear regression"""
        if len(historical_data) < 3:
            return None
        
        values = np.array(historical_data[-self.history_window:])
        
        # Try ML model first
        if self.models and sensor_name in self.models:
            try:
                model = self.models[sensor_name]
                scaler = self.scalers[sensor_name]
                
                # Scale input
                scaled_values = scaler.transform(values.reshape(-1, 1))
                X = scaled_values.reshape(1, -1)
                
                # Predict
                scaled_pred = model.predict(X)
                predicted = scaler.inverse_transform(scaled_pred.reshape(-1, 1))[0][0]
            except:
                # Fallback to linear regression
                predicted = self._linear_forecast(values, hours_ahead)
        else:
            # Linear regression fallback
            predicted = self._linear_forecast(values, hours_ahead)
        
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
            'trend': 'increasing' if change > 0 else 'decreasing',
            'alert': alert
        }
    
    def _linear_forecast(self, values, hours_ahead):
        """Fallback linear regression"""
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        slope, intercept = coeffs
        future_x = len(values) + (hours_ahead / 24)
        return slope * future_x + intercept

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
