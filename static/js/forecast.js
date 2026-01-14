// Hapag Farm - Forecasting Widget
function loadForecasts() {
    fetch('/api/forecast')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('forecast-alerts');
            if (!container) return;
            
            let html = '<div class="forecast-section">';
            html += '<h3 style="margin-bottom: 15px; color: #1f2937;">📊 Predictions (Next 24-72 Hours)</h3>';
            
            let hasAlerts = false;
            
            for (const [sensor, forecast] of Object.entries(data)) {
                if (forecast['24h']) {
                    const f24 = forecast['24h'];
                    const f72 = forecast['72h'];
                    
                    // Show prediction
                    const change24 = f24.change > 0 ? `+${f24.change.toFixed(1)}` : f24.change.toFixed(1);
                    const arrow = f24.trend === 'increasing' ? '📈' : '📉';
                    
                    html += `<div class="forecast-item" style="padding: 10px; margin: 8px 0; background: #f9fafb; border-left: 3px solid #3b82f6; border-radius: 4px;">`;
                    html += `<strong>${sensor}:</strong> ${f24.current.toFixed(1)} → ${f24.predicted.toFixed(1)} (${change24}) ${arrow}`;
                    
                    // Show alert if critical
                    if (f24.alert) {
                        html += `<div style="color: #dc2626; font-weight: 600; margin-top: 5px;">⚠️ ${f24.alert}</div>`;
                        hasAlerts = true;
                    } else if (f72.alert) {
                        html += `<div style="color: #f59e0b; margin-top: 5px;">⚠️ ${f72.alert}</div>`;
                        hasAlerts = true;
                    }
                    
                    html += '</div>';
                }
            }
            
            if (!hasAlerts) {
                html += '<p style="color: #10b981; font-weight: 500;">✓ All sensors within safe ranges</p>';
            }
            
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(err => console.error('Forecast error:', err));
}

// Auto-refresh every 5 minutes
setInterval(loadForecasts, 300000);
loadForecasts();
