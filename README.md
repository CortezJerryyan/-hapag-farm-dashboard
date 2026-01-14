# Hapag Farm Dashboard

A Flask-based agricultural monitoring and prediction dashboard for Filipino farmers using soil sensors and crop analytics.

## Features

- **Real-time Soil Monitoring**: Track nitrogen, phosphorus, potassium levels, pH, and humidity
- **Crop-Specific Recommendations**: Optimize crop growth with tailored guidance for Filipino crops
- **Predictive Analytics**: AI-powered crop yield predictions
- **Multi-language Support**: UI available in English and Filipino
- **Firebase Integration**: Real-time sensor data synchronization
- **Mobile App**: Flutter-based mobile application

## Prerequisites

- Python 3.10+
- Node.js (for frontend assets)
- Firebase account (for sensor data)
- Heroku account (for deployment)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/hapag-farm-dashboard.git
   cd hapag-farm-dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## Deployment

### Heroku Deployment

1. **Create Heroku account and app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

2. **Add GitHub secrets**
   - Go to repository Settings → Secrets and variables → Actions
   - Add these secrets:
     - `HEROKU_API_KEY`: Your Heroku API key
     - `HEROKU_APP_NAME`: Your Heroku app name
     - `HEROKU_EMAIL`: Your Heroku email

3. **Push to main branch**
   ```bash
   git push origin main
   ```
   
   GitHub Actions will automatically deploy your application!

## Project Structure

```
.
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku configuration
├── .github/
│   └── workflows/
│       ├── deploy.yml             # Deployment workflow
│       └── code-quality.yml       # Code quality checks
├── templates/                      # HTML templates
├── static/                         # CSS, JavaScript, images
├── hapag-farm-dashboard/          # Additional Flask variants
└── mobile_app/                     # Flutter mobile application
```

## Environment Variables

Create a `.env` file with:

```
FIREBASE_URL=your_firebase_url
FIREBASE_SECRET=your_firebase_secret
FLASK_ENV=production
DEBUG=False
```

## Available Routes

- `/` - Dashboard home page
- `/analytics` - Advanced analytics and reports
- `/predict` - Crop yield prediction tool
- `/settings` - User settings and preferences
- `/api/data` - API endpoint for sensor data

## Technologies Used

- **Backend**: Flask, scikit-learn, pandas, numpy
- **Frontend**: HTML5, CSS3, JavaScript, Plotly
- **Database**: Firebase Realtime Database
- **Mobile**: Flutter, Dart
- **Deployment**: Heroku, GitHub Actions
- **CI/CD**: GitHub Actions

## API Endpoints

### Get Sensor Data
```
GET /api/sensors
```

### Get Crop Recommendations
```
POST /api/recommendations
Content-Type: application/json

{
  "crop": "Sweet Potatoes",
  "soil_data": {
    "N": 85,
    "P": 25,
    "K": 105,
    "pH": 6.2,
    "humidity": 65
  }
}
```

## Testing

Run tests with:
```bash
pytest tests/ -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, email support@hapagfarm.com or open an issue on GitHub.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for Filipino agricultural community
- Sensor data integration with Firebase
- Crop database tailored for Philippine agriculture
