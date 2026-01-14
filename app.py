from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import requests
import joblib
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
import plotly.utils

app = Flask(__name__)

# Configuration
FIREBASE_URL = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_NODE = "/sensor_logs.json"

SOIL_THRESHOLDS = {
    "N": {"critical_low": 20, "optimal_min": 80, "optimal_max": 120, "critical_high": 200},
    "P": {"critical_low": 10, "optimal_min": 20, "optimal_max": 40, "critical_high": 60},
    "K": {"critical_low": 40, "optimal_min": 100, "optimal_max": 150, "critical_high": 200},
    "pH": {"critical_low": 5.0, "optimal_min": 6.0, "optimal_max": 7.0, "critical_high": 8.5},
    "humidity": {"critical_low": 30, "optimal_min": 50, "optimal_max": 70, "critical_high": 90}
}

DANGER_THRESHOLDS = {
    "N": 15, "P": 8, "K": 30,
    "pH_low": 4.5, "pH_high": 9.0,
    "humidity_low": 25, "humidity_high": 95
}

# Original Filipino Crop Database
CROP_DATABASE = {
    "Sweet Potatoes": {"N": (40, 80), "P": (15, 30), "K": (80, 120), "pH": (5.5, 6.5), "humidity": (60, 75)},
    "Munggo": {"N": (20, 60), "P": (15, 25), "K": (40, 80), "pH": (6.0, 7.5), "humidity": (60, 80)},
    "Peanuts": {"N": (20, 50), "P": (20, 35), "K": (60, 100), "pH": (6.0, 7.0), "humidity": (50, 70)},
    "Sitaw": {"N": (30, 70), "P": (20, 35), "K": (60, 100), "pH": (6.0, 7.5), "humidity": (65, 85)},
    "Tomatoes": {"N": (120, 180), "P": (30, 50), "K": (150, 200), "pH": (6.0, 7.0), "humidity": (60, 80)},
    "Lettuce": {"N": (80, 120), "P": (20, 35), "K": (100, 140), "pH": (6.0, 7.0), "humidity": (70, 85)},
    "Eggplant": {"N": (100, 150), "P": (25, 45), "K": (120, 180), "pH": (6.0, 7.0), "humidity": (60, 80)},
    "Chili": {"N": (80, 120), "P": (25, 40), "K": (100, 150), "pH": (6.0, 7.0), "humidity": (50, 70)},
    "Cabbage": {"N": (100, 140), "P": (25, 40), "K": (120, 160), "pH": (6.0, 7.0), "humidity": (65, 85)},
    "Bell Peppers": {"N": (100, 140), "P": (25, 45), "K": (120, 180), "pH": (6.0, 7.0), "humidity": (60, 80)},
    "Broccoli": {"N": (120, 160), "P": (30, 50), "K": (140, 180), "pH": (6.0, 7.0), "humidity": (65, 85)},
    "Corn": {"N": (100, 150), "P": (25, 45), "K": (100, 140), "pH": (6.0, 7.5), "humidity": (50, 70)},
    "Kangkong": {"N": (80, 120), "P": (15, 30), "K": (60, 100), "pH": (5.0, 7.0), "humidity": (75, 95)},
    "Mustasa": {"N": (80, 120), "P": (20, 35), "K": (100, 140), "pH": (6.0, 7.0), "humidity": (70, 85)},
    "Garlic": {"N": (60, 100), "P": (20, 35), "K": (80, 120), "pH": (6.0, 7.5), "humidity": (60, 75)},
    "Radish": {"N": (60, 100), "P": (15, 30), "K": (80, 120), "pH": (6.0, 7.0), "humidity": (65, 80)},
    "Carrots": {"N": (80, 120), "P": (20, 40), "K": (100, 140), "pH": (6.0, 7.0), "humidity": (65, 80)},
    "Potatoes": {"N": (100, 140), "P": (25, 45), "K": (120, 180), "pH": (5.5, 6.5), "humidity": (60, 80)},
    "Banana": {"N": (200, 300), "P": (30, 50), "K": (400, 600), "pH": (5.5, 7.0), "humidity": (75, 85)},
    "Onion": {"N": (80, 120), "P": (20, 40), "K": (100, 150), "pH": (6.0, 7.5), "humidity": (60, 75)},
    "Okra": {"N": (60, 100), "P": (20, 35), "K": (80, 120), "pH": (6.0, 7.5), "humidity": (50, 70)},
    "Bokchoy": {"N": (80, 120), "P": (20, 35), "K": (100, 140), "pH": (6.0, 7.0), "humidity": (70, 85)},
    "Rice": {"N": (80, 120), "P": (20, 40), "K": (80, 120), "pH": (5.5, 7.0), "humidity": (70, 90)}
}

# ML to Filipino crop mapping
ML_TO_FILIPINO = {
    "rice": "Rice", "maize": "Corn", "chickpea": "Munggo", "kidneybeans": "Sitaw",
    "pigeonpeas": "Peanuts", "mothbeans": "Sweet Potatoes", "mungbean": "Munggo",
    "blackgram": "Sitaw", "lentil": "Peanuts", "pomegranate": "Tomatoes",
    "banana": "Banana", "mango": "Banana", "grapes": "Tomatoes",
    "watermelon": "Cabbage", "muskmelon": "Cabbage", "apple": "Tomatoes",
    "orange": "Broccoli", "papaya": "Corn", "coconut": "Kangkong",
    "cotton": "Mustasa", "jute": "Garlic", "coffee": "Radish"
}

# Load ML Models
def load_ml_models():
    try:
        model = joblib.load('hapag_crop_model.pkl')
        encoder = joblib.load('label_encoder.pkl')
        return model, encoder, True
    except:
        return None, None, False

ml_model, label_encoder, model_loaded = load_ml_models()

# Helper Functions
def validate_input(value, min_val=0, max_val=1000):
    try:
        num_value = float(value)
        return min_val <= num_value <= max_val
    except:
        return False

def safe_ml_prediction(n, p, k, ph, hum):
    if not ml_model or not label_encoder:
        return None, 0
    
    try:
        if not all(validate_input(x) for x in [n, p, k]) or not validate_input(ph, 0, 14) or not validate_input(hum, 0, 100):
            return None, 0
            
        input_df = pd.DataFrame([[n, p, k, ph, hum]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
        prediction_idx = ml_model.predict(input_df)[0]
        
        available_classes = label_encoder.classes_
        
        if 0 <= prediction_idx < len(available_classes):
            ml_prediction = available_classes[prediction_idx]
            filipino_crop = ML_TO_FILIPINO.get(ml_prediction.lower(), ml_prediction.title())
            
            confidence = 85.0
            if hasattr(ml_model, "predict_proba"):
                try:
                    confidence = np.max(ml_model.predict_proba(input_df)) * 100
                except:
                    confidence = 85.0
            
            return filipino_crop, confidence
        else:
            return None, 0
            
    except Exception as e:
        return None, 0

def calculate_soil_health_score(n, p, k, ph, hum):
    def get_score(value, param_type):
        if param_type not in SOIL_THRESHOLDS:
            return 50
        thresholds = SOIL_THRESHOLDS[param_type]
        if thresholds["optimal_min"] <= value <= thresholds["optimal_max"]:
            return 100
        elif (thresholds["optimal_min"] - 20) <= value <= (thresholds["optimal_max"] + 20):
            return 80
        else:
            return 30
    
    scores = [get_score(n, "N"), get_score(p, "P"), get_score(k, "K"), 
              get_score(ph, "pH"), get_score(hum, "humidity")]
    return sum(scores) / len(scores)

def get_expert_recommendation(n, p, k, ph, hum):
    crop_scores = {}
    for crop, requirements in CROP_DATABASE.items():
        score = 0
        for param, (min_val, max_val) in requirements.items():
            if param == "pH":
                value = ph
            elif param == "humidity":
                value = hum
            else:
                value = locals()[param.lower()]
            
            if min_val <= value <= max_val:
                score += 2
            elif abs(value - min_val) <= 20 or abs(value - max_val) <= 20:
                score += 1
        
        crop_scores[crop] = (score / 10) * 100
    
    if crop_scores:
        best_crop = max(crop_scores, key=crop_scores.get)
        if crop_scores[best_crop] >= 40:
            return best_crop
    return "Rice"

def fetch_latest_data():
    try:
        url = f"{FIREBASE_URL}{FIREBASE_NODE}?orderBy=\"$key\"&limitToLast=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                key = list(data.keys())[0]
                values = data[key]
                timestamp = values.get('timestamp', values.get('date', 'Unknown'))
                
                # Map sensor field names to app field names
                mapped_values = {
                    'N': values.get('N', values.get('nitrogen', 0)),
                    'P': values.get('P', values.get('phosphorus', 0)),
                    'K': values.get('K', values.get('potassium', 0)),
                    'ph': values.get('ph', values.get('pH', 0)),
                    'humidity': values.get('humidity', 0),
                    'soil_moisture': values.get('soil_moisture', 0),
                    'temperature': values.get('temperature', 0),
                    'timestamp': timestamp
                }
                return mapped_values, timestamp
    except:
        pass
    return None, None

def fetch_firebase_data():
    try:
        response = requests.get(f"{FIREBASE_URL}{FIREBASE_NODE}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_weather_data(lat=None, lon=None):
    """Get weather data based on coordinates or default to Philippines"""
    # Default to Indang, Cavite if no coordinates provided
    if lat is None or lon is None:
        lat = 14.1953
        lon = 120.8769
    
    try:
        # Current weather and forecast
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,precipitation,weathercode,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia/Manila"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get('current_weather', {})
            hourly = data.get('hourly', {})
            daily = data.get('daily', {})
            
            # Get location name using reverse geocoding
            location_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            location_response = requests.get(location_url, timeout=5, headers={'User-Agent': 'HapagFarm/1.0'})
            location_name = "Philippines"
            
            if location_response.status_code == 200:
                location_data = location_response.json()
                address = location_data.get('address', {})
                location_name = address.get('city') or address.get('town') or address.get('municipality') or address.get('province', 'Philippines')
            
            # Weather code mapping
            weather_codes = {
                0: {"desc": "Clear sky", "icon": "☀️"},
                1: {"desc": "Mainly clear", "icon": "🌤️"},
                2: {"desc": "Partly cloudy", "icon": "⛅"},
                3: {"desc": "Overcast", "icon": "☁️"},
                45: {"desc": "Foggy", "icon": "🌫️"},
                48: {"desc": "Foggy", "icon": "🌫️"},
                51: {"desc": "Light drizzle", "icon": "🌦️"},
                53: {"desc": "Drizzle", "icon": "🌦️"},
                55: {"desc": "Heavy drizzle", "icon": "🌧️"},
                61: {"desc": "Light rain", "icon": "🌧️"},
                63: {"desc": "Rain", "icon": "🌧️"},
                65: {"desc": "Heavy rain", "icon": "⛈️"},
                80: {"desc": "Rain showers", "icon": "🌦️"},
                95: {"desc": "Thunderstorm", "icon": "⛈️"},
            }
            
            current_code = current.get('weathercode', 0)
            weather_info = weather_codes.get(current_code, {"desc": "Clear", "icon": "☀️"})
            
            # Hourly forecast (next 24 hours)
            hourly_forecast = []
            for i in range(0, min(24, len(hourly.get('time', []))), 3):
                hourly_forecast.append({
                    'time': hourly['time'][i].split('T')[1][:5] if 'T' in hourly['time'][i] else hourly['time'][i],
                    'temp': round(hourly['temperature_2m'][i]),
                    'icon': weather_codes.get(hourly.get('weathercode', [0])[i], {"icon": "☀️"})['icon'],
                    'precipitation': round(hourly.get('precipitation', [0])[i], 1)
                })
            
            # Daily forecast (next 7 days)
            daily_forecast = []
            days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            for i in range(min(7, len(daily.get('time', [])))):
                date_obj = datetime.strptime(daily['time'][i], '%Y-%m-%d')
                daily_forecast.append({
                    'day': days[date_obj.weekday()] if i > 0 else 'Today',
                    'icon': weather_codes.get(daily.get('weathercode', [0])[i], {"icon": "☀️"})['icon'],
                    'max_temp': round(daily['temperature_2m_max'][i]),
                    'min_temp': round(daily['temperature_2m_min'][i]),
                    'precipitation': round(daily.get('precipitation_sum', [0])[i], 1)
                })
            
            return {
                "location": location_name,
                "temperature": round(current.get('temperature', 28)),
                "feels_like": round(current.get('temperature', 28)),
                "description": weather_info['desc'],
                "icon": weather_info['icon'],
                "humidity": hourly.get('relativehumidity_2m', [65])[0],
                "wind_speed": round(current.get('windspeed', 8.2), 1),
                "precipitation": round(sum(hourly.get('precipitation', [0])[:24]), 1),
                "hourly": hourly_forecast,
                "daily": daily_forecast,
                "lat": lat,
                "lon": lon
            }
    except Exception as e:
        print(f"Weather error: {e}")
    
    # Fallback data
    return {
        "location": "Philippines",
        "temperature": 28,
        "feels_like": 30,
        "description": "Partly cloudy",
        "icon": "⛅",
        "humidity": 65,
        "wind_speed": 8.2,
        "precipitation": 12.3,
        "hourly": [],
        "daily": [],
        "lat": 14.1953,
        "lon": 120.8769
    }

def get_condition_flag(value, param_type):
    try:
        value = float(value)
        param_map = {'ph': 'pH', 'moisture': 'humidity'}
        param_type = param_map.get(param_type, param_type)
        
        if param_type in SOIL_THRESHOLDS:
            thresholds = SOIL_THRESHOLDS[param_type]
            if value < thresholds["critical_low"]:
                return "critical", "Critical: Too Low"
            elif value > thresholds["critical_high"]:
                return "critical", "Critical: Too High"
            elif thresholds["optimal_min"] <= value <= thresholds["optimal_max"]:
                return "optimal", "Optimal"
            else:
                return "warning", "Suboptimal"
    except:
        pass
    return "unknown", "Unknown"

def get_fertilizer_recommendation(n, p, k):
    recommendations = []
    
    if n < SOIL_THRESHOLDS["N"]["optimal_min"]:
        recommendations.append("Apply Nitrogen fertilizer (Urea 46-0-0): 50-100 kg/ha")
    elif n > SOIL_THRESHOLDS["N"]["optimal_max"]:
        recommendations.append("Reduce Nitrogen application")
    
    if p < SOIL_THRESHOLDS["P"]["optimal_min"]:
        recommendations.append("Apply Phosphorus fertilizer (DAP 18-46-0): 30-60 kg/ha")
    elif p > SOIL_THRESHOLDS["P"]["optimal_max"]:
        recommendations.append("Reduce Phosphorus application")
    
    if k < SOIL_THRESHOLDS["K"]["optimal_min"]:
        recommendations.append("Apply Potassium fertilizer (MOP 0-0-60): 40-80 kg/ha")
    elif k > SOIL_THRESHOLDS["K"]["optimal_max"]:
        recommendations.append("Reduce Potassium application")
    
    if not recommendations:
        recommendations.append("Nutrient levels are optimal")
    
    return recommendations

def create_trend_chart(data):
    if not data:
        return None
    
    try:
        # Process Firebase data structure
        processed_data = []
        for key, values in data.items():
            if isinstance(values, dict):
                # Extract timestamp and sensor values
                timestamp = values.get('timestamp', values.get('date', key))
                n_val = values.get('N', values.get('nitrogen', 0))
                p_val = values.get('P', values.get('phosphorus', 0))
                k_val = values.get('K', values.get('potassium', 0))
                ph_val = values.get('ph', values.get('pH', 0))
                hum_val = values.get('humidity', values.get('moisture', 0))
                
                try:
                    processed_data.append({
                        'timestamp': pd.to_datetime(timestamp),
                        'N': float(n_val) if n_val else 0,
                        'P': float(p_val) if p_val else 0,
                        'K': float(k_val) if k_val else 0,
                        'pH': float(ph_val) if ph_val else 0,
                        'humidity': float(hum_val) if hum_val else 0
                    })
                except:
                    continue
        
        if not processed_data:
            return None
        
        # Create DataFrame and sort by timestamp
        df = pd.DataFrame(processed_data)
        df = df.sort_values('timestamp')
        
        # Create the plot
        fig = go.Figure()
        
        # Add nutrient traces with cleaner styling
        nutrients = [
            ('N', '#10b981', 'Nitrogen'),
            ('P', '#f59e0b', 'Phosphorus'),
            ('K', '#3b82f6', 'Potassium')
        ]
        
        for nutrient, color, label in nutrients:
            if nutrient in df.columns and not df[nutrient].isna().all():
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df[nutrient],
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>{label}</b>: %{{y:.1f}}<extra></extra>'
                ))
        
        # Add pH and humidity on secondary y-axis with dashed lines
        if 'pH' in df.columns and not df['pH'].isna().all():
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['pH'],
                mode='lines',
                name='pH',
                line=dict(color='#ef4444', width=2, dash='dash'),
                yaxis='y2',
                hovertemplate='<b>pH</b>: %{y:.1f}<extra></extra>'
            ))
        
        if 'humidity' in df.columns and not df['humidity'].isna().all():
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['humidity'],
                mode='lines',
                name='Humidity',
                line=dict(color='#8b5cf6', width=2, dash='dot'),
                yaxis='y2',
                hovertemplate='<b>Humidity</b>: %{y:.0f}%<extra></extra>'
            ))
        
        # Update layout - cleaner and more organized
        fig.update_layout(
            title={
                'text': 'Sensor Trends',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#1f2937', 'family': 'Arial, sans-serif'}
            },
            xaxis={
                'title': 'Date',
                'showgrid': True,
                'gridcolor': '#f3f4f6',
                'tickformat': '%m/%d',
                'tickfont': {'size': 11}
            },
            yaxis={
                'title': 'NPK (ppm)',
                'showgrid': True,
                'gridcolor': '#f3f4f6',
                'side': 'left',
                'tickfont': {'size': 11},
                'range': [0, 200]
            },
            yaxis2={
                'title': 'pH / Humidity (%)',
                'overlaying': 'y',
                'side': 'right',
                'showgrid': False,
                'tickfont': {'size': 11},
                'range': [0, 100]
            },
            height=450,
            margin=dict(l=60, r=60, t=60, b=50),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
                font={'size': 11},
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#e5e7eb',
                borderwidth=1
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='white',
                font_size=12,
                font_family='Arial'
            )
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        print(f"Chart creation error: {e}")
        return None

def calculate_trend_analysis(data):
    """Calculate trend statistics for nutrients"""
    if not data:
        return {}
    
    try:
        # Process data similar to chart function
        processed_data = []
        for key, values in data.items():
            if isinstance(values, dict):
                timestamp = values.get('timestamp', values.get('date', key))
                n_val = values.get('N', values.get('nitrogen', 0))
                p_val = values.get('P', values.get('phosphorus', 0))
                k_val = values.get('K', values.get('potassium', 0))
                
                try:
                    processed_data.append({
                        'timestamp': pd.to_datetime(timestamp),
                        'N': float(n_val) if n_val else 0,
                        'P': float(p_val) if p_val else 0,
                        'K': float(k_val) if k_val else 0
                    })
                except:
                    continue
        
        if len(processed_data) < 2:
            return {'N': 'stable', 'P': 'stable', 'K': 'stable'}
        
        df = pd.DataFrame(processed_data).sort_values('timestamp')
        trends = {}
        
        for nutrient in ['N', 'P', 'K']:
            if nutrient in df.columns:
                recent_avg = df[nutrient].tail(3).mean()
                older_avg = df[nutrient].head(3).mean()
                
                if recent_avg > older_avg * 1.1:
                    trends[nutrient] = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    trends[nutrient] = 'decreasing'
                else:
                    trends[nutrient] = 'stable'
            else:
                trends[nutrient] = 'stable'
        
        return trends
    except:
        return {'N': 'stable', 'P': 'stable', 'K': 'stable'}

# Routes
@app.route('/')
def index():
    # Fetch real-time data
    data, timestamp = fetch_latest_data()
    
    # Default values (only used when no data)
    sensor_data = {
        'N': 0, 'P': 0, 'K': 0, 'ph': 0, 'humidity': 0,
        'soil_moisture': 0, 'temperature': 0,
        'timestamp': 'No data',
        'connected': False
    }
    
    if data:
        try:
            sensor_data.update({
                'N': float(data.get('N', 0)),
                'P': float(data.get('P', 0)),
                'K': float(data.get('K', 0)),
                'ph': float(data.get('ph', 0)),
                'humidity': float(data.get('humidity', 0)),
                'soil_moisture': float(data.get('soil_moisture', 0)),
                'temperature': float(data.get('temperature', 0)),
                'timestamp': timestamp or 'Unknown',
                'connected': True
            })
        except:
            sensor_data['connected'] = False
    
    # Calculate metrics
    health_score = calculate_soil_health_score(
        sensor_data['N'], sensor_data['P'], sensor_data['K'], 
        sensor_data['ph'], sensor_data['humidity']
    )
    
    # Get crop recommendation
    prediction_name, confidence = safe_ml_prediction(
        sensor_data['N'], sensor_data['P'], sensor_data['K'], 
        sensor_data['ph'], sensor_data['humidity']
    )
    
    if not prediction_name:
        prediction_name = get_expert_recommendation(
            sensor_data['N'], sensor_data['P'], sensor_data['K'], 
            sensor_data['ph'], sensor_data['humidity']
        )
        confidence = 0
    
    # Get weather data
    weather = get_weather_data()
    
    # Check for alerts
    alerts = []
    danger_count = 0
    
    if sensor_data['N'] < DANGER_THRESHOLDS["N"]:
        alerts.append("CRITICAL: Nitrogen severely depleted")
        danger_count += 1
    if sensor_data['P'] < DANGER_THRESHOLDS["P"]:
        alerts.append("CRITICAL: Phosphorus severely depleted")
        danger_count += 1
    if sensor_data['K'] < DANGER_THRESHOLDS["K"]:
        alerts.append("CRITICAL: Potassium severely depleted")
        danger_count += 1
    if sensor_data['ph'] < DANGER_THRESHOLDS["pH_low"] or sensor_data['ph'] > DANGER_THRESHOLDS["pH_high"]:
        alerts.append("CRITICAL: pH level dangerous")
        danger_count += 1
    if sensor_data['humidity'] < DANGER_THRESHOLDS["humidity_low"] or sensor_data['humidity'] > DANGER_THRESHOLDS["humidity_high"]:
        alerts.append("CRITICAL: Humidity level dangerous")
        danger_count += 1
    
    # Get fertilizer recommendations
    fertilizer_recs = get_fertilizer_recommendation(
        sensor_data['N'], sensor_data['P'], sensor_data['K']
    )
    
    return render_template('index.html', 
                         sensor_data=sensor_data,
                         health_score=health_score,
                         prediction_name=prediction_name,
                         confidence=confidence,
                         weather=weather,
                         alerts=alerts,
                         danger_count=danger_count,
                         fertilizer_recs=fertilizer_recs,
                         model_loaded=model_loaded)

@app.route('/analytics')
def analytics():
    data = fetch_firebase_data()
    
    # Check if we have any data
    has_data = data is not None and len(data) > 0
    
    chart_json = create_trend_chart(data) if has_data else None
    trends = calculate_trend_analysis(data) if has_data else {}
    
    # Fetch current sensor data for gauges (same as Dashboard)
    current_data, current_timestamp = fetch_latest_data()
    current_sensor = {
        'N': 0, 'P': 0, 'K': 0, 'ph': 0, 'humidity': 0
    }
    if current_data:
        try:
            current_sensor = {
                'N': float(current_data.get('N', 0)),
                'P': float(current_data.get('P', 0)),
                'K': float(current_data.get('K', 0)),
                'ph': float(current_data.get('ph', 0)),
                'humidity': float(current_data.get('humidity', 0))
            }
        except:
            pass
    
    # Calculate summary statistics
    summary_stats = {}
    if has_data:
        try:
            values = []
            for key, entry in data.items():
                if isinstance(entry, dict):
                    values.append({
                        'N': float(entry.get('N', 0)),
                        'P': float(entry.get('P', 0)),
                        'K': float(entry.get('K', 0)),
                        'pH': float(entry.get('ph', 0)),
                        'humidity': float(entry.get('humidity', 0))
                    })
            
            if values:
                df_stats = pd.DataFrame(values)
                summary_stats = {
                    'total_readings': len(values),
                    'avg_N': df_stats['N'].mean(),
                    'avg_P': df_stats['P'].mean(),
                    'avg_K': df_stats['K'].mean(),
                    'avg_pH': df_stats['pH'].mean(),
                    'avg_humidity': df_stats['humidity'].mean()
                }
        except:
            pass
    
    return render_template('analytics.html', 
                         chart_json=chart_json,
                         has_data=data is not None,
                         trends=trends,
                         summary_stats=summary_stats,
                         current_sensor=current_sensor)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            n_in = float(request.form['nitrogen'])
            p_in = float(request.form['phosphorus'])
            k_in = float(request.form['potassium'])
            ph_in = float(request.form['ph'])
            hum_in = float(request.form['humidity'])
            
            # Get prediction
            prediction_name, confidence = safe_ml_prediction(n_in, p_in, k_in, ph_in, hum_in)
            
            if not prediction_name:
                prediction_name = get_expert_recommendation(n_in, p_in, k_in, ph_in, hum_in)
                confidence = 0
            
            # Get fertilizer recommendations
            fertilizer_recs = get_fertilizer_recommendation(n_in, p_in, k_in)
            
            # Get condition flags
            ph_status, ph_msg = get_condition_flag(ph_in, 'pH')
            hum_status, hum_msg = get_condition_flag(hum_in, 'humidity')
            
            return render_template('predict.html',
                                 prediction_name=prediction_name,
                                 confidence=confidence,
                                 fertilizer_recs=fertilizer_recs,
                                 ph_status=ph_status,
                                 ph_msg=ph_msg,
                                 hum_status=hum_status,
                                 hum_msg=hum_msg,
                                 form_data={
                                     'nitrogen': n_in,
                                     'phosphorus': p_in,
                                     'potassium': k_in,
                                     'ph': ph_in,
                                     'humidity': hum_in
                                 })
        except:
            return render_template('predict.html', error="Invalid input values")
    
    return render_template('predict.html')

@app.route('/settings')
def settings():
    return render_template('settings.html', 
                         model_loaded=model_loaded,
                         firebase_url=FIREBASE_URL,
                         firebase_node=FIREBASE_NODE)

@app.route('/ml_models')
def ml_models():
    """ML Model Comparison Page"""
    return render_template('ml_models.html')

@app.route('/api/refresh')
def api_refresh():
    data, timestamp = fetch_latest_data()
    
    if data:
        try:
            sensor_data = {
                'N': float(data.get('N', 40)),
                'P': float(data.get('P', 20)),
                'K': float(data.get('K', 60)),
                'ph': float(data.get('ph', 6.5)),
                'humidity': float(data.get('humidity', 55)),
                'timestamp': timestamp,
                'connected': True
            }
            return jsonify(sensor_data)
        except:
            pass
    
    return jsonify({'connected': False})

@app.route('/api/test_connection')
def api_test_connection():
    data = fetch_firebase_data()
    if data:
        return jsonify({'success': True, 'count': len(data)})
    return jsonify({'success': False})

@app.route('/api/weather')
def api_weather():
    """API endpoint for weather with location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    weather = get_weather_data(lat, lon)
    return jsonify(weather)

@app.route('/api/analytics_data')
def api_analytics_data():
    """API endpoint for real-time analytics updates"""
    data = fetch_firebase_data()
    trends = calculate_trend_analysis(data)
    
    return jsonify({
        'trends': trends,
        'has_data': data is not None,
        'data_count': len(data) if data else 0
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)