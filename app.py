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
                return values, timestamp
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
    """Create separate charts for NPK, pH, and Humidity for mobile-friendly display"""
    if not data:
        return None
    
    try:
        # Process Firebase data and filter out zeros
        processed_data = []
        for key, values in data.items():
            if isinstance(values, dict):
                timestamp = values.get('timestamp', values.get('date', key))
                n_val = values.get('N', values.get('nitrogen', 0))
                p_val = values.get('P', values.get('phosphorus', 0))
                k_val = values.get('K', values.get('potassium', 0))
                ph_val = values.get('ph', values.get('pH', 0))
                hum_val = values.get('humidity', values.get('moisture', 0))
                
                try:
                    if any([n_val, p_val, k_val, ph_val, hum_val]):
                        processed_data.append({
                            'timestamp': pd.to_datetime(timestamp),
                            'N': float(n_val) if n_val else None,
                            'P': float(p_val) if p_val else None,
                            'K': float(k_val) if k_val else None,
                            'pH': float(ph_val) if ph_val else None,
                            'humidity': float(hum_val) if hum_val else None
                        })
                except:
                    continue
        
        if not processed_data:
            return None
        
        df = pd.DataFrame(processed_data).sort_values('timestamp')
        
        # Create individual charts as JSON objects
        charts = {}
        
        # NPK Chart
        fig_npk = go.Figure()
        if df['N'].notna().any():
            fig_npk.add_trace(go.Scatter(
                x=df['timestamp'], y=df['N'],
                mode='lines+markers',
                name='Nitrogen',
                line=dict(color='#10b981', width=2),
                marker=dict(size=4),
                connectgaps=False
            ))
        if df['P'].notna().any():
            fig_npk.add_trace(go.Scatter(
                x=df['timestamp'], y=df['P'],
                mode='lines+markers',
                name='Phosphorus',
                line=dict(color='#f59e0b', width=2),
                marker=dict(size=4),
                connectgaps=False
            ))
        if df['K'].notna().any():
            fig_npk.add_trace(go.Scatter(
                x=df['timestamp'], y=df['K'],
                mode='lines+markers',
                name='Potassium',
                line=dict(color='#3b82f6', width=2),
                marker=dict(size=4),
                connectgaps=False
            ))
        
        fig_npk.update_layout(
            title=dict(text='N, P, K Nutrients', font=dict(color='#000', size=14)),
            xaxis=dict(title='Date', showgrid=True, gridcolor='#f3f4f6', 
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            yaxis=dict(title='mg/kg', showgrid=True, gridcolor='#f3f4f6',
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            height=250,
            margin=dict(l=45, r=25, t=40, b=35),
            paper_bgcolor='white',
            plot_bgcolor='white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(size=9, color='#000')),
            hovermode='x unified'
        )
        charts['npk'] = json.dumps(fig_npk, cls=plotly.utils.PlotlyJSONEncoder)
        
        # pH Chart
        fig_ph = go.Figure()
        if df['pH'].notna().any():
            fig_ph.add_trace(go.Scatter(
                x=df['timestamp'], y=df['pH'],
                mode='lines+markers',
                name='pH Level',
                line=dict(color='#ef4444', width=2, dash='dash'),
                marker=dict(size=4),
                connectgaps=False
            ))
        
        fig_ph.update_layout(
            title=dict(text='Soil pH', font=dict(color='#000', size=14)),
            xaxis=dict(title='Date', showgrid=True, gridcolor='#f3f4f6',
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            yaxis=dict(title='pH Level', range=[0, 14], showgrid=True, gridcolor='#f3f4f6',
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            height=250,
            margin=dict(l=45, r=25, t=40, b=35),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            hovermode='x unified'
        )
        charts['ph'] = json.dumps(fig_ph, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Humidity Chart
        fig_hum = go.Figure()
        if df['humidity'].notna().any():
            fig_hum.add_trace(go.Scatter(
                x=df['timestamp'], y=df['humidity'],
                mode='lines+markers',
                name='Humidity',
                line=dict(color='#06b6d4', width=2),
                marker=dict(size=4),
                connectgaps=False
            ))
        
        fig_hum.update_layout(
            title=dict(text='Humidity', font=dict(color='#000', size=14)),
            xaxis=dict(title='Date', showgrid=True, gridcolor='#f3f4f6',
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            yaxis=dict(title='%', range=[0, 100], showgrid=True, gridcolor='#f3f4f6',
                      title_font=dict(color='#000', size=11), tickfont=dict(color='#000', size=9)),
            height=250,
            margin=dict(l=45, r=25, t=40, b=35),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            hovermode='x unified'
        )
        charts['humidity'] = json.dumps(fig_hum, cls=plotly.utils.PlotlyJSONEncoder)
        
        return charts
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

def calculate_eda_data(data):
    """Calculate EDA statistics: correlation matrix and box plot data"""
    if not data:
        return None
    
    try:
        processed_data = []
        for key, values in data.items():
            if isinstance(values, dict):
                n_val = values.get('N', values.get('nitrogen', 0))
                p_val = values.get('P', values.get('phosphorus', 0))
                k_val = values.get('K', values.get('potassium', 0))
                ph_val = values.get('ph', values.get('pH', 0))
                hum_val = values.get('humidity', values.get('moisture', 0))
                
                try:
                    processed_data.append({
                        'N': float(n_val) if n_val else 0,
                        'P': float(p_val) if p_val else 0,
                        'K': float(k_val) if k_val else 0,
                        'Soil_pH': float(ph_val) if ph_val else 0,
                        'Humidity': float(hum_val) if hum_val else 0
                    })
                except:
                    continue
        
        if len(processed_data) < 2:
            return None
        
        df = pd.DataFrame(processed_data)
        
        # Calculate correlation matrix
        corr_matrix = df.corr()
        
        # Calculate box plot statistics (quartiles)
        box_stats = {}
        for col in df.columns:
            box_stats[col] = {
                'min': float(df[col].min()),
                'q1': float(df[col].quantile(0.25)),
                'median': float(df[col].median()),
                'q3': float(df[col].quantile(0.75)),
                'max': float(df[col].max())
            }
        
        return {
            'correlation': corr_matrix.to_dict(),
            'box_stats': box_stats
        }
    except Exception as e:
        print(f"EDA calculation error: {e}")
        return None

# Routes
@app.route('/')
def index():
    # Fetch real-time data
    data, timestamp = fetch_latest_data()
    
    # Default values
    sensor_data = {
        'N': 40, 'P': 20, 'K': 60, 'ph': 6.5, 'humidity': 55,
        'timestamp': timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'connected': False
    }
    
    if data:
        try:
            sensor_data.update({
                'N': float(data.get('N', 40)),
                'P': float(data.get('P', 20)),
                'K': float(data.get('K', 60)),
                'ph': float(data.get('ph', 6.5)),
                'humidity': float(data.get('humidity', 55)),
                'connected': True
            })
        except:
            pass
    
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
    chart_data = create_trend_chart(data)
    trends = calculate_trend_analysis(data)
    eda_data = calculate_eda_data(data)
    
    # Calculate summary statistics
    summary_stats = {}
    if data:
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
                         chart_data=chart_data,
                         has_data=data is not None,
                         trends=trends,
                         summary_stats=summary_stats,
                         eda_data=eda_data)

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