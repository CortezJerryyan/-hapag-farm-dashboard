import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION (MUST BE FIRST)
# =========================================================
st.set_page_config(
    page_title="Hapag Farm Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CONFIGURATION
# =========================================================
FIREBASE_URL = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_NODE = "/sensor_logs.json"

# =========================================================
# CUSTOM CSS STYLING
# =========================================================
st.markdown("""
<style>
    :root {
        --primary-green: #2E7D32;
        --light-green: #4CAF50;
        --accent-green: #81C784;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--light-green) 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD ML MODELS
# =========================================================
@st.cache_resource
def load_ml_models():
    try:
        model = joblib.load('hapag_crop_model.pkl')
        encoder = joblib.load('label_encoder.pkl')
        return model, encoder, True
    except Exception:
        return None, None, False

ml_model, label_encoder, model_loaded = load_ml_models()

# =========================================================
# EXPERT SYSTEM
# =========================================================
CROP_RULES = {
    "N_LOW": ["Sweet Potatoes", "Munggo", "Peanuts", "Sitaw"],
    "N_HIGH": ["Tomatoes", "Lettuce", "Eggplant", "Chili", "Corn"],
    "P_LOW": ["Lettuce", "Garlic", "Radish"],
    "P_HIGH": ["Cabbage", "Carrots", "Potatoes"],
    "K_LOW": ["Sweet Potatoes"],
    "K_HIGH": ["Banana", "Kangkong"],
    "PH_ACIDIC": ["Potatoes", "Kangkong"], 
    "PH_ALKALINE": ["Onion", "Okra", "Garlic"],
    "HUM_DRY": ["Okra", "Eggplant", "Chili"],
    "HUM_WET": ["Rice", "Kangkong"]
}

def get_expert_recommendation(n, p, k, ph, hum):
    scores = {}
    candidates = []
    
    if n < 100: candidates += CROP_RULES["N_LOW"]
    elif n > 150: candidates += CROP_RULES["N_HIGH"]
    
    if p < 15: candidates += CROP_RULES["P_LOW"]
    elif p > 30: candidates += CROP_RULES["P_HIGH"]
    
    if ph < 6.0: candidates += CROP_RULES["PH_ACIDIC"]
    elif ph > 7.0: candidates += CROP_RULES["PH_ALKALINE"]
    
    for crop in candidates:
        scores[crop] = scores.get(crop, 0) + 1
    
    if not scores: return "General Crops (Conditions are Balanced)"
    return max(scores, key=scores.get)

# =========================================================
# DATA FUNCTIONS
# =========================================================
@st.cache_data(ttl=30)
def fetch_firebase_data():
    try:
        response = requests.get(f"{FIREBASE_URL}{FIREBASE_NODE}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def fetch_latest_data():
    try:
        url = f"{FIREBASE_URL}{FIREBASE_NODE}?orderBy=\"$key\"&limitToLast=1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200 and response.json():
            data = response.json()
            key = list(data.keys())[0]
            values = data[key]
            
            if 'timestamp' in values:
                ts = values['timestamp']
            elif 'date' in values:
                ts = values['date']
            else:
                ts = "Unknown Date (Real-time)"
                
            return values, ts
    except Exception:
        return None, None
    return None, None

def get_condition_flag(value, type):
    if type == 'ph':
        if value < 5.5: return "red", "Critical: Too Acidic"
        if value > 7.5: return "red", "Critical: Too Alkaline"
        return "green", "Optimal"
        
    if type == 'moisture':
        if value < 40: return "red", "Critical: Too Dry"
        if value > 85: return "red", "Critical: Too Wet"
        return "green", "Optimal"

    if type in ['N', 'P', 'K']:
        if value < 20: return "red", "Critical: Depleted"
        if value > 200: return "orange", "Warning: High Concentration"
        return "green", "Sufficient"
    
    return "gray", "Unknown"

# =========================================================
# MAIN HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🌾 Hapag Farm Dashboard</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Real-time Soil Monitoring & Crop Recommendation System</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #81C784; margin-bottom: 1rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🌾</div>
        <h2 style="margin: 0; color: #2E7D32;">Hapag Farm</h2>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">Smart Agriculture Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    if model_loaded:
        st.success("✅ ML Model Loaded")
    else:
        st.warning("⚠️ Running in Rule-Based Mode")

# =========================================================
# MAIN TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(["📡 Real-Time Monitoring", "📅 Historical Data", "🎛️ Manual Prediction"])

# =========================================================
# REAL-TIME MONITORING
# =========================================================
with tab1:
    st.header("📡 Real-Time Sensor Readings")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()

    # Initialize defaults
    n, p, k = 0, 0, 0
    ph, hum = 7.0, 50.0
    timestamp = "Checking..."
    connection_status = False

    # Fetch data
    data, ts = fetch_latest_data()
    
    if data:
        n = float(data.get('N', 0))
        p = float(data.get('P', 0))
        k = float(data.get('K', 0))
        ph = float(data.get('ph', 7))
        hum = float(data.get('humidity', 50))
        timestamp = ts
        connection_status = True
    else:
        connection_status = False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Display status
    if connection_status:
        st.info(f"📅 Data Timestamp: *{timestamp}*", icon="🕒")
    else:
        st.warning(f"⚠️ Offline Mode. Showing default values. Last check: *{timestamp}*", icon="📡")

    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    def display_metric(col, label, value, unit, type):
        color, msg = get_condition_flag(value, type)
        col.metric(label, f"{value} {unit}")
        if color == "red":
            col.error(msg, icon="🚩")
        elif color == "orange":
            col.warning(msg, icon="⚠️")
        else:
            col.success(msg, icon="✅")

    display_metric(col1, "Nitrogen", n, "mg/kg", 'N')
    display_metric(col2, "Phosphorus", p, "mg/kg", 'P')
    display_metric(col3, "Potassium", k, "mg/kg", 'K')
    display_metric(col4, "pH Level", ph, "", 'ph')
    display_metric(col5, "Humidity", hum, "%", 'moisture')

    st.divider()

    # AI PREDICTION (ORIGINAL LOGIC)
    st.subheader("🌱 Crop Recommendation")
    
    if ml_model:
        try:
            # Use exact column names from original training: N, P, K, Soil_pH, Humidity
            input_df = pd.DataFrame([[n, p, k, ph, hum]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
            prediction_idx = ml_model.predict(input_df)[0]
            prediction_name = label_encoder.inverse_transform([prediction_idx])[0]
            
            # Confidence score
            if hasattr(ml_model, "predict_proba"):
                confidence = np.max(ml_model.predict_proba(input_df)) * 100
            else:
                confidence = 100.0
            
            c1, c2 = st.columns([1, 3])
            c1.metric("Recommended Crop", prediction_name)
            c1.caption(f"Confidence: {confidence:.2f}%")
            
            # Contextual Insight with Date
            if connection_status:
                c2.success(f"*Insight:* Based on soil data from *{timestamp}*, *{prediction_name}* is the most suitable crop.")
            else:
                c2.warning(f"*Insight:* Based on *default/simulated values*, the model suggests *{prediction_name}*.")
            
        except Exception as e:
            st.error(f"Prediction Error: {e}")
    else:
        rec = get_expert_recommendation(n, p, k, ph, hum)
        st.info(f"*Rule-Based Recommendation:* {rec}")

# =========================================================
# HISTORICAL DATA
# =========================================================
with tab2:
    st.header("📅 Historical Data Analysis")
    
    data = fetch_firebase_data()
    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df.dropna().sort_index()
        
        if not df.empty:
            fig = go.Figure()
            
            if 'N' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['N'],
                    mode='lines+markers',
                    name='Nitrogen',
                    line=dict(color='#4CAF50', width=3)
                ))
            
            if 'P' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['P'],
                    mode='lines+markers',
                    name='Phosphorus',
                    line=dict(color='#FF9800', width=3)
                ))
            
            if 'K' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['K'],
                    mode='lines+markers',
                    name='Potassium',
                    line=dict(color='#2196F3', width=3)
                ))
            
            fig.update_layout(
                title="Nutrient Levels Over Time",
                xaxis_title="Date",
                yaxis_title="Concentration (mg/kg)",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data available for analysis.")
    else:
        st.warning("Unable to fetch historical data.")

# =========================================================
# MANUAL PREDICTION
# =========================================================
with tab3:
    st.header("🎛️ Manual Soil Simulation")
    st.write("Adjust the sliders to simulate different soil conditions.")
    
    col1, col2 = st.columns(2)
    with col1:
        n_in = st.slider("Nitrogen (N)", 0, 140, 40)
        p_in = st.slider("Phosphorus (P)", 0, 140, 40)
        k_in = st.slider("Potassium (K)", 0, 200, 40)
    with col2:
        ph_in = st.slider("pH Level", 0.0, 14.0, 6.5)
        hum_in = st.slider("Humidity (%)", 0, 100, 50)
        
    if st.button("🔍 Analyze Soil"):
        st.divider()
        st.subheader("Results")
        
        # Flags
        f1, f2 = st.columns(2)
        c_ph, m_ph = get_condition_flag(ph_in, 'ph')
        c_hum, m_hum = get_condition_flag(hum_in, 'moisture')
        
        if c_ph == 'red': f1.error(f"pH: {m_ph}")
        else: f1.success(f"pH: {m_ph}")
            
        if c_hum == 'red': f2.error(f"Moisture: {m_hum}")
        else: f2.success(f"Moisture: {m_hum}")
        
        # Prediction
        if ml_model:
            input_df = pd.DataFrame([[n_in, p_in, k_in, ph_in, hum_in]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
            pred = label_encoder.inverse_transform(ml_model.predict(input_df))[0]
            st.success(f"### Recommended Crop: {pred}")
        else:
            rec = get_expert_recommendation(n_in, p_in, k_in, ph_in, hum_in)
            st.success(f"### Recommended Crop: {rec}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🌾 <strong>Hapag Farm Dashboard</strong> | Smart Agriculture Monitoring System
</div>
""", unsafe_allow_html=True)