import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib

# Page config MUST be first
st.set_page_config(page_title="Hapag Farm", page_icon="🌾", layout="wide")

# Configuration
FIREBASE_URL = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_NODE = "/sensor_logs.json"

# Load ML models
@st.cache_resource
def load_models():
    try:
        model = joblib.load('hapag_crop_model.pkl')
        encoder = joblib.load('label_encoder.pkl')
        return model, encoder, True
    except:
        return None, None, False

ml_model, label_encoder, model_loaded = load_models()

# Expert system rules
def get_expert_recommendation(n, p, k, ph, hum):
    if ph < 6.0:
        return "Potatoes (Acid-tolerant)"
    elif ph > 7.5:
        return "Onions (Alkaline-tolerant)"
    elif hum > 70:
        return "Rice (High moisture)"
    else:
        return "Tomatoes (Balanced conditions)"

# Fetch data
@st.cache_data(ttl=30)
def fetch_data():
    try:
        response = requests.get(f"{FIREBASE_URL}{FIREBASE_NODE}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_latest():
    try:
        url = f"{FIREBASE_URL}{FIREBASE_NODE}?orderBy=\"$key\"&limitToLast=1"
        response = requests.get(url, timeout=3)
        if response.status_code == 200 and response.json():
            data = response.json()
            key = list(data.keys())[0]
            return data[key], key
    except:
        pass
    return None, None

# Header
st.title("🌾 Hapag Farm Dashboard")

# Sidebar
with st.sidebar:
    st.header("🌾 Hapag Farm")
    if model_loaded:
        st.success("✅ ML Model Loaded")
    else:
        st.warning("⚠️ Rule-Based Mode")

# Tabs
tab1, tab2, tab3 = st.tabs(["📡 Real-Time", "📅 Historical", "🎛️ Manual"])

# Tab 1: Real-Time
with tab1:
    st.header("📡 Real-Time Monitoring")
    
    # Get data
    data, timestamp = get_latest()
    
    if data:
        n = float(data.get('N', 0))
        p = float(data.get('P', 0))
        k = float(data.get('K', 0))
        ph = float(data.get('ph', 7))
        hum = float(data.get('humidity', 50))
        
        st.info(f"📅 Last Updated: {timestamp}")
    else:
        n, p, k, ph, hum = 0, 0, 0, 7.0, 50.0
        st.warning("⚠️ Using default values")
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Nitrogen", f"{n} mg/kg")
    col2.metric("Phosphorus", f"{p} mg/kg")
    col3.metric("Potassium", f"{k} mg/kg")
    col4.metric("pH Level", f"{ph}")
    col5.metric("Humidity", f"{hum}%")
    
    st.divider()
    
    # Prediction
    st.subheader("🌱 Crop Recommendation")
    
    if ml_model:
        try:
            # Use correct column names from training
            input_df = pd.DataFrame([[n, p, k, ph, hum]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
            prediction_idx = ml_model.predict(input_df)[0]
            crop_name = label_encoder.inverse_transform([prediction_idx])[0]
            
            if hasattr(ml_model, "predict_proba"):
                confidence = np.max(ml_model.predict_proba(input_df)) * 100
            else:
                confidence = 100.0
            
            c1, c2 = st.columns([1, 3])
            c1.metric("Recommended Crop", crop_name)
            c1.caption(f"Confidence: {confidence:.1f}%")
            c2.success(f"Based on current soil conditions, {crop_name} is recommended.")
            
        except Exception as e:
            st.error(f"Prediction Error: {e}")
    else:
        rec = get_expert_recommendation(n, p, k, ph, hum)
        st.info(f"Rule-Based Recommendation: {rec}")

# Tab 2: Historical
with tab2:
    st.header("📅 Historical Data")
    
    data = fetch_data()
    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        st.line_chart(df[['N', 'P', 'K']] if all(col in df.columns for col in ['N', 'P', 'K']) else None)
    else:
        st.warning("No historical data available")

# Tab 3: Manual
with tab3:
    st.header("🎛️ Manual Prediction")
    
    col1, col2 = st.columns(2)
    with col1:
        n_in = st.slider("Nitrogen", 0, 200, 50)
        p_in = st.slider("Phosphorus", 0, 100, 25)
        k_in = st.slider("Potassium", 0, 200, 100)
    with col2:
        ph_in = st.slider("pH Level", 0.0, 14.0, 6.5)
        hum_in = st.slider("Humidity", 0, 100, 60)
    
    if st.button("🔮 Get Recommendation"):
        if ml_model:
            try:
                input_df = pd.DataFrame([[n_in, p_in, k_in, ph_in, hum_in]], columns=['N', 'P', 'K', 'Soil_pH', 'Humidity'])
                pred = label_encoder.inverse_transform(ml_model.predict(input_df))[0]
                st.success(f"Recommended Crop: {pred}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            rec = get_expert_recommendation(n_in, p_in, k_in, ph_in, hum_in)
            st.success(f"Recommended Crop: {rec}")

st.markdown("---")
st.markdown("🌾 **Hapag Farm Dashboard** - Smart Agriculture System")