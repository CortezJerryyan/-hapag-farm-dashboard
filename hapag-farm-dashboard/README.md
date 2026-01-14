# 🌾 Hapag Farm Dashboard

A Streamlit-based dashboard for real-time farm monitoring and AI-powered crop recommendations.

## 📁 Project Structure

```
hapag-farm-dashboard/
│── app.py                 # Main Streamlit application
│── hapag_crop_model.pkl   # ML model (from Google Colab)
│── label_encoder.pkl      # Label encoder (from Google Colab)
│── requirements.txt       # Python dependencies
│── setup.bat             # Windows setup script
└── README.md             # This file
```

## 🚀 Quick Start

### Step 1: Add Model Files
Download these files from your Google Colab and place them in this folder:
- `hapag_crop_model.pkl`
- `label_encoder.pkl`

### Step 2: Setup Environment
Run the setup script:
```bash
setup.bat
```

Or manually:
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run Dashboard
```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Run Streamlit
streamlit run app.py
```

## 🔧 Configuration

### Firebase Settings
The app connects to:
- URL: `https://hapagfarm-default-rtdb.asia-southeast1.firebasedatabase.app`
- Node: `/sensor_logs.json`

### Model Status
- ✅ **ML Model Loaded**: Both .pkl files found and loaded successfully
- ⚠️ **Rule-Based Mode**: Model files missing, using basic rules

## 📊 Features

1. **Real-time Data**: Live sensor readings from Firebase
2. **Historical Analysis**: Time-series charts and trends
3. **Crop Prediction**: AI-powered recommendations based on environmental data

## 🐛 Troubleshooting

**Model not loading?**
- Ensure `hapag_crop_model.pkl` and `label_encoder.pkl` are in the same folder as `app.py`
- Check file names match exactly

**Firebase connection issues?**
- Verify internet connection
- Check Firebase URL and permissions

**Dependencies issues?**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again