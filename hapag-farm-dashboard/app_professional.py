import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# =========================================================
# CUSTOM CSS STYLING
# =========================================================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-green: #2E7D32;
        --light-green: #4CAF50;
        --accent-green: #81C784;
        --bg-light: #F1F8E9;
        --text-dark: #1B5E20;
        --card-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: var(--card-shadow);
        border-left: 4px solid var(--light-green);
        margin: 0.5rem 0;
    }
    
    /* Status banners */
    .status-banner {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .status-success {
        background: linear-gradient(90deg, #E8F5E8 0%, #C8E6C9 100%);
        border-left: 4px solid var(--light-green);
        color: var(--text-dark);
    }
    
    .status-warning {
        background: linear-gradient(90deg, #FFF3E0 0%, #FFE0B2 100%);
        border-left: 4px solid #FF9800;
        color: #E65100;
    }
    
    .status-info {
        background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left: 4px solid #2196F3;
        color: #0D47A1;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid var(--accent-green);
        margin-bottom: 1rem;
    }
    
    .sidebar-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--light-green) 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Recommendation card */
    .recommendation-card {
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid var(--light-green);
        text-align: center;
        margin: 1rem 0;
    }
    
    .crop-name {
        font-size: 2rem;
        font-weight: bold;
        color: var(--primary-green);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONFIGURATION
# =========================================================
FIREBASE_URL = "https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_NODE = "/sensor_logs.json"

# Page Configuration
st.set_page_config(
    page_title="Hapag Farm Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# DATA FETCHING FUNCTIONS
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

def get_latest_reading():
    data = fetch_firebase_data()
    if data:
        latest_key = max(data.keys())
        return data[latest_key], latest_key
    return None, None

# =========================================================
# UI COMPONENTS
# =========================================================
def render_status_banner(status_type, message, icon=""):
    if status_type == "success":
        st.markdown(f"""
        <div class="status-banner status-success">
            {icon} {message}
        </div>
        """, unsafe_allow_html=True)
    elif status_type == "warning":
        st.markdown(f"""
        <div class="status-banner status-warning">
            {icon} {message}
        </div>
        """, unsafe_allow_html=True)
    elif status_type == "info":
        st.markdown(f"""
        <div class="status-banner status-info">
            {icon} {message}
        </div>
        """, unsafe_allow_html=True)

def render_metric_card(title, value, unit, status, icon):
    color = "#4CAF50" if status == "optimal" else "#FF9800" if status == "warning" else "#F44336"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h4 style="margin: 0; color: #666;">{title}</h4>
                <h2 style="margin: 0.5rem 0; color: {color};">{value} {unit}</h2>
            </div>
            <div style="font-size: 2rem;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_recommendation_card(crop_name, confidence=None, method="AI"):
    confidence_text = f"Confidence: {confidence:.1f}%" if confidence else ""
    method_badge = "🤖 AI Prediction" if method == "AI" else "📋 Rule-Based"
    
    st.markdown(f"""
    <div class="recommendation-card">
        <div style="font-size: 1.2rem; color: #666; margin-bottom: 1rem;">{method_badge}</div>
        <div class="crop-name">🌱 {crop_name}</div>
        <div style="color: #666; font-size: 1.1rem;">{confidence_text}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">🌾</div>
        <h2 style="margin: 0; color: #2E7D32;">Hapag Farm</h2>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">Smart Agriculture Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    page = st.radio(
        "📍 Navigation",
        ["🏠 Dashboard", "📊 Analytics", "🔮 Prediction", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System Status
    st.markdown("**🔧 System Status**")
    if model_loaded:
        render_status_banner("success", "AI Model Active", "✅")
    else:
        render_status_banner("warning", "Rule-Based Mode", "⚠️")
    
    # Connection Status
    data = fetch_firebase_data()
    if data:
        render_status_banner("success", "Database Connected", "🔗")
    else:
        render_status_banner("warning", "Database Offline", "📡")

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
# DASHBOARD PAGE
# =========================================================
if page == "🏠 Dashboard":
    # Get latest data
    latest_data, timestamp = get_latest_reading()
    
    if latest_data:
        # Data timestamp
        render_status_banner("info", f"📅 Last Updated: {timestamp}", "🕒")
        
        # Sensor readings in cards
        st.markdown("### 📊 Current Sensor Readings")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            n_val = latest_data.get('N', 0)
            n_status = "optimal" if 50 <= n_val <= 150 else "warning" if n_val < 20 else "critical"
            render_metric_card("Nitrogen", n_val, "mg/kg", n_status, "🧪")
        
        with col2:
            p_val = latest_data.get('P', 0)
            p_status = "optimal" if 15 <= p_val <= 30 else "warning" if p_val < 10 else "critical"
            render_metric_card("Phosphorus", p_val, "mg/kg", p_status, "⚗️")
        
        with col3:
            k_val = latest_data.get('K', 0)
            k_status = "optimal" if 80 <= k_val <= 200 else "warning" if k_val < 40 else "critical"
            render_metric_card("Potassium", k_val, "mg/kg", k_status, "🔬")
        
        with col4:
            ph_val = latest_data.get('ph', 7.0)
            ph_status = "optimal" if 6.0 <= ph_val <= 7.5 else "warning"
            render_metric_card("pH Level", ph_val, "", ph_status, "🌡️")
        
        with col5:
            hum_val = latest_data.get('humidity', 50)
            hum_status = "optimal" if 40 <= hum_val <= 70 else "warning"
            render_metric_card("Humidity", hum_val, "%", hum_status, "💧")
        
        st.markdown("---")
        
        # Crop Recommendation
        st.markdown("### 🌱 Crop Recommendation")
        
        if model_loaded and ml_model:
            try:
                # AI Prediction
                features = np.array([[n_val, p_val, k_val, ph_val, hum_val]])
                prediction = ml_model.predict(features)[0]
                crop_name = label_encoder.inverse_transform([prediction])[0]
                
                confidence = None
                if hasattr(ml_model, 'predict_proba'):
                    confidence = np.max(ml_model.predict_proba(features)) * 100
                
                render_recommendation_card(crop_name, confidence, "AI")
                
            except Exception as e:
                st.error(f"Prediction error: {e}")
        else:
            # Rule-based fallback
            if ph_val < 6.0:
                crop_name = "Potatoes (Acid-tolerant)"
            elif ph_val > 7.5:
                crop_name = "Onions (Alkaline-tolerant)"
            elif hum_val > 70:
                crop_name = "Rice (High moisture)"
            else:
                crop_name = "Tomatoes (Balanced conditions)"
            
            render_recommendation_card(crop_name, method="Rule")
    
    else:
        render_status_banner("warning", "No sensor data available. Please check your IoT device connection.", "📡")

# =========================================================
# ANALYTICS PAGE
# =========================================================
elif page == "📊 Analytics":
    st.markdown("### 📈 Historical Data Analysis")
    
    data = fetch_firebase_data()
    if data:
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df.dropna().sort_index()
        
        if not df.empty:
            # Time series chart
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
            
            # Summary statistics
            st.markdown("### 📋 Summary Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Nitrogen", f"{df['N'].mean():.1f} mg/kg")
            with col2:
                st.metric("Avg Phosphorus", f"{df['P'].mean():.1f} mg/kg")
            with col3:
                st.metric("Avg Potassium", f"{df['K'].mean():.1f} mg/kg")
        else:
            render_status_banner("info", "No historical data available for analysis.", "📊")
    else:
        render_status_banner("warning", "Unable to fetch historical data.", "📡")

# =========================================================
# PREDICTION PAGE
# =========================================================
elif page == "🔮 Prediction":
    st.markdown("### 🎛️ Manual Crop Prediction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_input = st.number_input("Nitrogen (mg/kg)", 0, 300, 100)
        p_input = st.number_input("Phosphorus (mg/kg)", 0, 100, 25)
        k_input = st.number_input("Potassium (mg/kg)", 0, 400, 150)
    
    with col2:
        ph_input = st.number_input("pH Level", 0.0, 14.0, 6.5, 0.1)
        hum_input = st.number_input("Humidity (%)", 0, 100, 60)
    
    if st.button("🔮 Get Recommendation", type="primary"):
        if model_loaded and ml_model:
            try:
                features = np.array([[n_input, p_input, k_input, ph_input, hum_input]])
                prediction = ml_model.predict(features)[0]
                crop_name = label_encoder.inverse_transform([prediction])[0]
                
                confidence = None
                if hasattr(ml_model, 'predict_proba'):
                    confidence = np.max(ml_model.predict_proba(features)) * 100
                
                render_recommendation_card(crop_name, confidence, "AI")
                
            except Exception as e:
                st.error(f"Prediction error: {e}")
        else:
            # Rule-based prediction
            if ph_input < 6.0:
                crop_name = "Potatoes (Acid-tolerant)"
            elif ph_input > 7.5:
                crop_name = "Onions (Alkaline-tolerant)"
            elif hum_input > 70:
                crop_name = "Rice (High moisture)"
            else:
                crop_name = "Tomatoes (Balanced conditions)"
            
            render_recommendation_card(crop_name, method="Rule")

# =========================================================
# SETTINGS PAGE
# =========================================================
elif page == "⚙️ Settings":
    st.markdown("### ⚙️ System Configuration")
    
    st.markdown("**🔧 Model Information**")
    if model_loaded:
        st.success("✅ Machine Learning model is loaded and active")
        st.info("The system is using AI-powered crop recommendations based on your trained model.")
    else:
        st.warning("⚠️ ML model files not found")
        st.info("The system is running in rule-based mode. To enable AI predictions, add these files to your project folder:")
        st.code("hapag_crop_model.pkl\nlabel_encoder.pkl")
    
    st.markdown("**🔗 Database Connection**")
    st.code(f"Firebase URL: {FIREBASE_URL}")
    st.code(f"Data Node: {FIREBASE_NODE}")
    
    if st.button("🔄 Test Connection"):
        data = fetch_firebase_data()
        if data:
            st.success("✅ Successfully connected to Firebase database")
            st.info(f"Found {len(data)} sensor readings")
        else:
            st.error("❌ Unable to connect to Firebase database")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🌾 <strong>Hapag Farm Dashboard</strong> | Smart Agriculture Monitoring System
</div>
""", unsafe_allow_html=True)