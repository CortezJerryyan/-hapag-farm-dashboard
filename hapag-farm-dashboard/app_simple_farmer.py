import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
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
# SIMPLE CSS
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-image: url("hapag.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(2px);
        pointer-events: none;
        z-index: -1;
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
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
# SIMPLE FUNCTIONS
# =========================================================
CROP_RULES = {
    "N_LOW": ["Sweet Potatoes", "Munggo", "Peanuts"],
    "N_HIGH": ["Tomatoes", "Lettuce", "Corn"],
    "P_LOW": ["Lettuce", "Garlic"],
    "P_HIGH": ["Cabbage", "Potatoes"],
    "PH_ACIDIC": ["Potatoes"], 
    "PH_ALKALINE": ["Onion", "Garlic"],
    "HUM_WET": ["Rice", "Kangkong"]
}

def get_simple_recommendation(n, p, k, ph, hum):
    if ph < 6.0:
        return "Potatoes (good for acidic soil)"
    elif ph > 7.5:
        return "Onions (good for alkaline soil)"
    elif hum > 70:
        return "Rice (good for wet conditions)"
    elif n > 100:
        return "Corn (needs lots of nitrogen)"
    else:
        return "Tomatoes (balanced conditions)"

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
                ts = "Real-time"
                
            return values, ts
    except Exception:
        return None, None
    return None, None

def get_soil_status(value, nutrient_type):
    if nutrient_type in ['N', 'P', 'K']:
        if value < 20:
            return "🔴 Low - Need fertilizer"
        elif value > 150:
            return "🟡 High - Reduce fertilizer"
        else:
            return "🟢 Good"
    elif nutrient_type == 'ph':
        if value < 5.5:
            return "🔴 Too acidic - Add lime"
        elif value > 7.5:
            return "🔴 Too alkaline - Add sulfur"
        else:
            return "🟢 Good"
    elif nutrient_type == 'humidity':
        if value < 40:
            return "🔴 Too dry - Need water"
        elif value > 80:
            return "🔴 Too wet - Improve drainage"
        else:
            return "🟢 Good"

def get_simple_fertilizer_advice(n, p, k):
    advice = []
    if n < 60:
        advice.append("🌱 Add Urea fertilizer for Nitrogen")
    if p < 15:
        advice.append("🌱 Add DAP fertilizer for Phosphorus")
    if k < 80:
        advice.append("🌱 Add Muriate of Potash for Potassium")
    
    if not advice:
        advice.append("🌱 Your soil nutrients are good!")
    
    return advice

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🌾 Hapag Farm</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Simple Soil Monitor for Farmers</p>
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
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">Easy Farming Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    if model_loaded:
        st.success("✅ Smart System ON")
    else:
        st.warning("⚠️ Basic Mode")

# =========================================================
# SIMPLE TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(["📱 Check Soil Now", "📊 History", "🎛️ Test Different Soil"])

# =========================================================
# TAB 1: CURRENT SOIL
# =========================================================
with tab1:
    st.header("📱 Check Your Soil Right Now")
    
    if st.button("🔄 Get Fresh Reading", type="primary"):
        st.cache_data.clear()

    # Get current data
    data, timestamp = fetch_latest_data()
    
    if data:
        n = float(data.get('N', 0))
        p = float(data.get('P', 0))
        k = float(data.get('K', 0))
        ph = float(data.get('ph', 7))
        hum = float(data.get('humidity', 50))
        
        st.success(f"📅 Last reading: {timestamp}")
    else:
        # Default values when no data
        n, p, k, ph, hum = 85, 22, 135, 6.8, 65
        st.warning("📡 Using sample data - connect your sensors for real readings")

    # Show soil readings in simple way
    st.subheader("🌱 Your Soil Condition")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Nitrogen (N)", f"{n} mg/kg")
        st.markdown(get_soil_status(n, 'N'))
        
    with col2:
        st.metric("Phosphorus (P)", f"{p} mg/kg")
        st.markdown(get_soil_status(p, 'P'))
        
    with col3:
        st.metric("Potassium (K)", f"{k} mg/kg")
        st.markdown(get_soil_status(k, 'K'))

    col4, col5 = st.columns(2)
    
    with col4:
        st.metric("pH Level", f"{ph}")
        st.markdown(get_soil_status(ph, 'ph'))
        
    with col5:
        st.metric("Moisture", f"{hum}%")
        st.markdown(get_soil_status(hum, 'humidity'))

    st.divider()

    # Simple crop recommendation
    st.subheader("🌾 What Crop Should You Plant?")
    
    if ml_model:
        try:
            input_df = pd.DataFrame([[n, p, k, ph, hum]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
            prediction_idx = ml_model.predict(input_df)[0]
            crop_name = label_encoder.inverse_transform([prediction_idx])[0]
            
            if hasattr(ml_model, "predict_proba"):
                confidence = np.max(ml_model.predict_proba(input_df)) * 100
            else:
                confidence = 95
            
            st.success(f"🌱 **Best crop for your soil: {crop_name}**")
            st.info(f"Confidence: {confidence:.0f}% sure this will grow well")
            
        except Exception as e:
            crop_name = get_simple_recommendation(n, p, k, ph, hum)
            st.success(f"🌱 **Recommended crop: {crop_name}**")
    else:
        crop_name = get_simple_recommendation(n, p, k, ph, hum)
        st.success(f"🌱 **Recommended crop: {crop_name}**")

    # Simple fertilizer advice
    st.subheader("🌱 What Fertilizer Do You Need?")
    
    fertilizer_advice = get_simple_fertilizer_advice(n, p, k)
    for advice in fertilizer_advice:
        st.markdown(advice)

# =========================================================
# TAB 2: SIMPLE HISTORY
# =========================================================
with tab2:
    st.header("📊 How Your Soil Changed Over Time")
    
    data = fetch_firebase_data()
    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df.dropna().sort_index()
        
        if not df.empty and len(df) > 1:
            # Simple chart
            fig = go.Figure()
            
            if 'N' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['N'],
                    mode='lines+markers',
                    name='Nitrogen',
                    line=dict(color='#4CAF50', width=4)
                ))
            
            if 'P' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['P'],
                    mode='lines+markers',
                    name='Phosphorus',
                    line=dict(color='#FF9800', width=4)
                ))
            
            if 'K' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['K'],
                    mode='lines+markers',
                    name='Potassium',
                    line=dict(color='#2196F3', width=4)
                ))
            
            fig.update_layout(
                title="Your Soil Nutrients Over Time",
                xaxis_title="Date",
                yaxis_title="Amount (mg/kg)",
                template='plotly_white',
                height=400,
                font=dict(size=14)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Simple summary
            st.subheader("📋 Simple Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'N' in df.columns:
                    avg_n = df['N'].mean()
                    st.metric("Average Nitrogen", f"{avg_n:.0f} mg/kg")
                    if avg_n < 60:
                        st.markdown("🔴 Usually low - add more nitrogen fertilizer")
                    else:
                        st.markdown("🟢 Usually good")
            
            with col2:
                if 'P' in df.columns:
                    avg_p = df['P'].mean()
                    st.metric("Average Phosphorus", f"{avg_p:.0f} mg/kg")
                    if avg_p < 20:
                        st.markdown("🔴 Usually low - add more phosphorus fertilizer")
                    else:
                        st.markdown("🟢 Usually good")
            
            with col3:
                if 'K' in df.columns:
                    avg_k = df['K'].mean()
                    st.metric("Average Potassium", f"{avg_k:.0f} mg/kg")
                    if avg_k < 80:
                        st.markdown("🔴 Usually low - add more potassium fertilizer")
                    else:
                        st.markdown("🟢 Usually good")
        else:
            st.info("📊 Not enough data yet. Keep monitoring your soil to see trends!")
    else:
        st.warning("📡 No history data available. Make sure your sensors are connected.")

# =========================================================
# TAB 3: TEST DIFFERENT SOIL
# =========================================================
with tab3:
    st.header("🎛️ Test Different Soil Conditions")
    st.write("Move the sliders to see what would happen with different soil.")
    
    col1, col2 = st.columns(2)
    with col1:
        n_test = st.slider("Nitrogen", 0, 200, 85, help="Higher = more nitrogen in soil")
        p_test = st.slider("Phosphorus", 0, 100, 25, help="Higher = more phosphorus in soil")
        k_test = st.slider("Potassium", 0, 200, 120, help="Higher = more potassium in soil")
    with col2:
        ph_test = st.slider("pH Level", 4.0, 9.0, 6.5, 0.1, help="6.0-7.0 is best for most crops")
        hum_test = st.slider("Moisture %", 20, 90, 60, help="50-70% is good for most crops")
        
    if st.button("🔍 See What Crop Grows Best", type="primary"):
        st.divider()
        
        # Show what would happen
        st.subheader("🌾 Results for This Soil")
        
        if ml_model:
            try:
                input_df = pd.DataFrame([[n_test, p_test, k_test, ph_test, hum_test]], 
                                      columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
                prediction_idx = ml_model.predict(input_df)[0]
                crop_name = label_encoder.inverse_transform([prediction_idx])[0]
                st.success(f"🌱 **Best crop: {crop_name}**")
            except:
                crop_name = get_simple_recommendation(n_test, p_test, k_test, ph_test, hum_test)
                st.success(f"🌱 **Best crop: {crop_name}**")
        else:
            crop_name = get_simple_recommendation(n_test, p_test, k_test, ph_test, hum_test)
            st.success(f"🌱 **Best crop: {crop_name}**")
        
        # Show soil condition
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Soil Condition:**")
            st.markdown(f"Nitrogen: {get_soil_status(n_test, 'N')}")
            st.markdown(f"Phosphorus: {get_soil_status(p_test, 'P')}")
            st.markdown(f"Potassium: {get_soil_status(k_test, 'K')}")
        
        with col2:
            st.markdown("**What to do:**")
            fertilizer_advice = get_simple_fertilizer_advice(n_test, p_test, k_test)
            for advice in fertilizer_advice:
                st.markdown(advice)

# =========================================================
# SIMPLE FOOTER
# =========================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🌾 <strong>Hapag Farm</strong> - Simple Smart Farming for Everyone
</div>
""", unsafe_allow_html=True)