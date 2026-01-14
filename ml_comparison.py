# Hapag Farm - ML Model Comparison & Visualization
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc, top_k_accuracy_score
from sklearn.impute import SimpleImputer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import base64
from io import BytesIO

def generate_ml_comparison():
    """Generate ML model comparison charts and metrics"""
    
    # Load dataset
    df = pd.read_csv('crop_yield_dataset.csv')
    keep_cols = ['N', 'P', 'K', 'Soil_pH', 'Humidity', 'Crop_Type']
    df_clean = df[keep_cols].copy()
    
    sensor_features = ['N', 'P', 'K', 'Soil_pH', 'Humidity']
    df_clean[sensor_features] = df_clean[sensor_features].replace(0, np.nan)
    imputer = SimpleImputer(strategy='median')
    df_clean[sensor_features] = imputer.fit_transform(df_clean[sensor_features])
    
    X = df_clean[sensor_features]
    y = df_clean['Crop_Type']
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    classes = label_encoder.classes_
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    
    # Train models
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42)
    }
    
    model_scores = {}
    metrics_data = []
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)
        
        # Metrics
        test_acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        top_k = top_k_accuracy_score(y_test, y_prob, k=min(3, len(classes)))
        
        model_scores[name] = {
            'val_acc': cv_scores.mean(),
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        metrics_data.append([name, cv_scores.mean(), test_acc, prec, rec, f1, top_k, cv_scores.mean(), cv_scores.std()])
    
    metrics_df = pd.DataFrame(metrics_data, columns=['Model', 'Val Acc', 'Test Acc', 'Precision', 'Recall', 'F1-Score', 'Top-K Acc', 'CV Mean', 'CV Std'])
    
    # Generate charts
    charts = {}
    
    # Chart 1: Performance Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    main_cols = ['Model', 'Val Acc', 'Test Acc', 'Precision', 'Recall', 'F1-Score']
    metrics_long = pd.melt(metrics_df[main_cols], id_vars="Model", var_name="Metric", value_name="Score")
    
    sns.barplot(data=metrics_long, x="Metric", y="Score", hue="Model", palette="viridis", ax=ax1)
    ax1.set_title("Model Performance Comparison", fontsize=14, fontweight='bold')
    ax1.set_ylim(0.7, 1.0)
    ax1.legend(loc='lower right')
    ax1.grid(axis='y', alpha=0.3)
    
    x_pos = np.arange(len(metrics_df))
    bars = ax2.bar(x_pos, metrics_df['CV Mean'], yerr=metrics_df['CV Std'], capsize=10, alpha=0.7, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(metrics_df['Model'], fontweight='bold')
    ax2.set_ylabel('Accuracy', fontweight='bold')
    ax2.set_title('Cross-Validation Scores (5-Fold)', fontsize=14, fontweight='bold')
    ax2.set_ylim(0.7, 1.0)
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, mean in zip(bars, metrics_df['CV Mean']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{mean:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    charts['performance'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # Chart 2: ROC-AUC
    plt.figure(figsize=(10, 8))
    y_test_bin = label_binarize(y_test, classes=range(len(classes)))
    
    for name, model in models.items():
        y_prob = model.predict_proba(X_test)
        fpr, tpr, _ = roc_curve(y_test_bin.ravel(), y_prob.ravel())
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=2, label=f'{name} (AUC = {roc_auc:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random Classifier')
    plt.xlabel('False Positive Rate', fontweight='bold', fontsize=12)
    plt.ylabel('True Positive Rate', fontweight='bold', fontsize=12)
    plt.title('ROC-AUC Curve Comparison', fontsize=14, fontweight='bold')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    charts['roc'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return metrics_df, charts
