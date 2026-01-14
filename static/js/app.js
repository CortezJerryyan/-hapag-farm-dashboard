// Hapag Farm Dashboard JavaScript - Mobile Enhanced

// Global variables
let refreshInterval;
let isAutoRefresh = false;
let isMobile = window.innerWidth <= 768;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    detectMobile();
    initializePWA();
    
    // Start auto-refresh on page load
    startAutoRefresh();
});

function initializeApp() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize health score circles
    initializeHealthScores();
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Initialize mobile navigation
    initializeMobileNav();
    
    // Initialize auto-refresh if enabled
    const autoRefreshEnabled = localStorage.getItem('autoRefresh') === 'true';
    if (autoRefreshEnabled) {
        startAutoRefresh();
    }
    
    // Add mobile-specific event listeners
    addMobileEventListeners();
}

function detectMobile() {
    isMobile = window.innerWidth <= 768;
    
    // Add mobile class to body
    if (isMobile) {
        document.body.classList.add('mobile-device');
        
        // Disable zoom on mobile
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        // Prevent double-tap zoom
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(e) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
}

function initializeMobileNav() {
    // Set active navigation item
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.bottom-nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href.includes('index'))) {
            item.classList.add('active');
        }
    });
    
    // Add haptic feedback for mobile navigation
    navItems.forEach(item => {
        item.addEventListener('touchstart', function() {
            if (navigator.vibrate) {
                navigator.vibrate(50); // Light haptic feedback
            }
            this.style.transform = 'scale(0.95)';
        });
        
        item.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

function addMobileEventListeners() {
    // Swipe gestures for navigation
    let startX, startY, distX, distY;
    const threshold = 100; // Minimum distance for swipe
    
    document.addEventListener('touchstart', function(e) {
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
    });
    
    document.addEventListener('touchmove', function(e) {
        if (!startX || !startY) return;
        
        const touch = e.touches[0];
        distX = touch.clientX - startX;
        distY = touch.clientY - startY;
    });
    
    document.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;
        
        // Horizontal swipe detection
        if (Math.abs(distX) > Math.abs(distY) && Math.abs(distX) > threshold) {
            if (distX > 0) {
                // Swipe right - go to previous page
                navigateSwipe('prev');
            } else {
                // Swipe left - go to next page
                navigateSwipe('next');
            }
        }
        
        // Reset values
        startX = startY = distX = distY = null;
    });
    
    // Pull to refresh
    let startY_refresh, currentY, pullDistance;
    const refreshThreshold = 100;
    
    document.addEventListener('touchstart', function(e) {
        if (window.scrollY === 0) {
            startY_refresh = e.touches[0].clientY;
        }
    });
    
    document.addEventListener('touchmove', function(e) {
        if (startY_refresh && window.scrollY === 0) {
            currentY = e.touches[0].clientY;
            pullDistance = currentY - startY_refresh;
            
            if (pullDistance > 0 && pullDistance < refreshThreshold * 2) {
                e.preventDefault();
                // Visual feedback for pull to refresh
                document.body.style.transform = `translateY(${pullDistance * 0.5}px)`;
            }
        }
    });
    
    document.addEventListener('touchend', function(e) {
        if (pullDistance > refreshThreshold) {
            refreshData();
        }
        
        // Reset transform
        document.body.style.transform = '';
        startY_refresh = currentY = pullDistance = null;
    });
}

function navigateSwipe(direction) {
    const pages = ['/', '/analytics', '/predict', '/settings'];
    const currentPath = window.location.pathname;
    let currentIndex = pages.indexOf(currentPath);
    
    if (currentIndex === -1) currentIndex = 0;
    
    if (direction === 'next' && currentIndex < pages.length - 1) {
        window.location.href = pages[currentIndex + 1];
    } else if (direction === 'prev' && currentIndex > 0) {
        window.location.href = pages[currentIndex - 1];
    }
}

function initializePWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered:', registration);
            })
            .catch(error => {
                console.log('SW registration failed:', error);
            });
    }
    
    // Handle install prompt
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Show install button
        showInstallPrompt();
    });
    
    // Handle app installed
    window.addEventListener('appinstalled', (evt) => {
        console.log('App installed');
        hideInstallPrompt();
    });
}

function showInstallPrompt() {
    const installBanner = document.createElement('div');
    installBanner.id = 'installBanner';
    installBanner.className = 'alert alert-info position-fixed';
    installBanner.style.cssText = 'top: 70px; left: 1rem; right: 1rem; z-index: 1040;';
    installBanner.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <strong>Install Hapag Farm</strong><br>
                <small>Add to home screen for better experience</small>
            </div>
            <div>
                <button class="btn btn-primary btn-sm me-2" onclick="installApp()">Install</button>
                <button class="btn btn-outline-secondary btn-sm" onclick="hideInstallPrompt()">×</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(installBanner);
}

function hideInstallPrompt() {
    const banner = document.getElementById('installBanner');
    if (banner) {
        banner.remove();
    }
}

function installApp() {
    const banner = document.getElementById('installBanner');
    if (banner) {
        banner.remove();
    }
    
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            }
            deferredPrompt = null;
        });
    }
}

function initializeHealthScores() {
    const healthCircles = document.querySelectorAll('.health-circle');
    healthCircles.forEach(circle => {
        const score = circle.dataset.score || 0;
        circle.style.setProperty('--score', score);
        
        // Animate the circle
        setTimeout(() => {
            circle.style.background = `conic-gradient(
                var(--success-green) 0deg,
                var(--success-green) ${score * 3.6}deg,
                var(--border-light) ${score * 3.6}deg,
                var(--border-light) 360deg
            )`;
        }, 500);
    });
}

function addLoadingStates() {
    const buttons = document.querySelectorAll('button[type="submit"], .btn-refresh');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
                
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }, 2000);
            }
        });
    });
}

// Auto-refresh functionality - Check every 10 seconds
function startAutoRefresh() {
    if (isAutoRefresh) return;
    
    isAutoRefresh = true;
    const interval = 10000; // 10 seconds
    
    refreshInterval = setInterval(() => {
        refreshData();
    }, interval);
    
    // Update UI
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-pause me-1"></i>Pause';
        refreshBtn.onclick = stopAutoRefresh;
    }
}

function stopAutoRefresh() {
    if (!isAutoRefresh) return;
    
    isAutoRefresh = false;
    clearInterval(refreshInterval);
    
    // Update UI
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh';
        refreshBtn.onclick = startAutoRefresh;
    }
}

// Store last values to detect changes
let lastSensorValues = {};

function refreshData() {
    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (data.connected) {
                // Check if values changed
                const valuesChanged = hasValuesChanged(data);
                
                if (valuesChanged) {
                    // Update sensor values
                    updateSensorValues(data);
                    updateConnectionStatus(true);
                    lastSensorValues = {...data};
                } else {
                    // Values didn't change - sensor might be offline
                    updateConnectionStatus(false);
                }
            } else {
                updateConnectionStatus(false);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateConnectionStatus(false);
        });
}

function hasValuesChanged(newData) {
    if (Object.keys(lastSensorValues).length === 0) {
        return true; // First load
    }
    
    // Check if any sensor value changed
    const keys = ['N', 'P', 'K', 'ph', 'humidity'];
    for (let key of keys) {
        if (newData[key] !== lastSensorValues[key]) {
            return true;
        }
    }
    
    return false;
}

function updateConnectionStatus(isConnected) {
    const badge = document.querySelector('.badge');
    if (badge) {
        if (isConnected) {
            badge.className = 'badge bg-success me-2';
            badge.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
        } else {
            badge.className = 'badge bg-danger me-2';
            badge.innerHTML = '<i class="fas fa-wifi me-1"></i>Offline';
        }
    }
}

function updateSensorValues(data) {
    // Update metric cards
    const metrics = ['N', 'P', 'K', 'ph', 'humidity'];
    metrics.forEach(metric => {
        const card = document.querySelector(`[data-param="${metric}"]`);
        if (card && data[metric] !== undefined) {
            const valueElement = card.querySelector('.metric-value');
            if (valueElement) {
                const unit = metric === 'ph' ? '' : (metric === 'humidity' ? '%' : 'mg/kg');
                valueElement.innerHTML = `${data[metric]} <span class="metric-unit">${unit}</span>`;
            }
            
            // Update progress bar
            const progressBar = card.querySelector('.progress-bar');
            if (progressBar) {
                const maxValues = {N: 200, P: 60, K: 200, ph: 14, humidity: 100};
                const percentage = (data[metric] / maxValues[metric]) * 100;
                progressBar.style.width = `${Math.min(percentage, 100)}%`;
            }
        }
    });
    
    // Update timestamp
    const timestampElement = document.querySelector('.timestamp');
    if (timestampElement && data.timestamp) {
        timestampElement.textContent = data.timestamp;
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed fade-in`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    
    notification.innerHTML = `
        <i class="fas fa-${icons[type]} me-2"></i>${message}
        <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function formatNumber(num, decimals = 1) {
    return parseFloat(num).toFixed(decimals);
}

function getParameterStatus(value, param) {
    const thresholds = {
        'N': {critical_low: 20, optimal_min: 80, optimal_max: 120, critical_high: 200},
        'P': {critical_low: 10, optimal_min: 20, optimal_max: 40, critical_high: 60},
        'K': {critical_low: 40, optimal_min: 100, optimal_max: 150, critical_high: 200},
        'pH': {critical_low: 5.0, optimal_min: 6.0, optimal_max: 7.0, critical_high: 8.5},
        'humidity': {critical_low: 30, optimal_min: 50, optimal_max: 70, critical_high: 90}
    };
    
    const threshold = thresholds[param];
    if (!threshold) return 'unknown';
    
    if (value < threshold.critical_low || value > threshold.critical_high) {
        return 'critical';
    } else if (value < threshold.optimal_min || value > threshold.optimal_max) {
        return 'warning';
    } else {
        return 'optimal';
    }
}

// Export functions for CSV
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', filename);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => row[header]).join(','))
    ].join('\n');
    
    return csvContent;
}

// Local storage helpers
function savePreference(key, value) {
    localStorage.setItem(key, value);
}

function getPreference(key, defaultValue = null) {
    return localStorage.getItem(key) || defaultValue;
}

// Mobile-specific functions
function isMobile() {
    return window.innerWidth <= 768;
}

function optimizeForMobile() {
    if (isMobile()) {
        // Add mobile-specific optimizations
        document.body.classList.add('mobile-view');
        
        // Adjust chart sizes
        const charts = document.querySelectorAll('.chart-container');
        charts.forEach(chart => {
            chart.style.height = '300px';
        });
    }
}

// Initialize mobile optimizations
window.addEventListener('resize', optimizeForMobile);
optimizeForMobile();

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        refreshData();
    }
    
    // Escape to close modals/notifications
    if (e.key === 'Escape') {
        const notifications = document.querySelectorAll('.alert.position-fixed');
        notifications.forEach(notification => notification.remove());
    }
});

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}