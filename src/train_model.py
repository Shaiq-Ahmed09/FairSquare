"""
train_model.py
--------------
Trains an XGBoost regression model to predict Fair Market Value (FMV)
across the merged Chennai / Delhi / Pune dataset.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

from preprocess import preprocess

# ── Paths ─────────────────────────────────────────────────────────────────────
V21_PATH     = 'dataset/Real Estate Data V21.csv'
DELHI_PATH   = 'dataset/Delhi_v2.csv'
PUNE_PATH    = 'dataset/pune_house_prices.csv'
KOLKATA_PATH = 'dataset/Kolkata_real_estate.csv'
MODEL_DIR  = 'models'
MODEL_PATH   = os.path.join(MODEL_DIR, 'fmv_model.pkl')
ENCODER_PATH = os.path.join(MODEL_DIR, 'encoders.pkl')

FEATURES = [
    'Total_Area', 'BHK', 'Baths', 'Balcony_Enc',
    'Price_per_SQFT', 'City_Enc', 'Property_Type_Enc', 'Source_Enc',
]
TARGET = 'Price_INR'


def encode_categoricals(df: pd.DataFrame):
    encoders = {}
    for col, key in [('City', 'city'), ('Property_Type', 'property_type'), ('Source', 'source')]:
        le = LabelEncoder()
        df[f'{col}_Enc'] = le.fit_transform(df[col].astype(str))
        encoders[key] = le
    return df, encoders


def train(v21_path=V21_PATH, delhi_path=DELHI_PATH, pune_path=PUNE_PATH, kolkata_path=KOLKATA_PATH):
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Load & encode ──────────────────────────────────────────────────────────
    df = preprocess(v21_path, delhi_path, pune_path, kolkata_path)
    df, encoders = encode_categoricals(df)

    X = df[FEATURES]
    y = df[TARGET]

    print(f"\n[TRAIN] Total rows: {len(df)} | Features: {FEATURES}")
    print(f"        City distribution:\n{df['City'].value_counts().to_string()}")

    # ── Split ──────────────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model = xgb.XGBRegressor(
        n_estimators    = 600,
        learning_rate   = 0.04,
        max_depth       = 7,
        subsample       = 0.8,
        colsample_bytree= 0.8,
        reg_alpha       = 0.1,
        reg_lambda      = 1.0,
        random_state    = 42,
        n_jobs          = -1,
        verbosity       = 0,
    )

    print("[TRAIN] Fitting XGBoost...")
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # ── Metrics ───────────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    print(f"\n{'='*50}")
    print(f"  MODEL PERFORMANCE")
    print(f"{'='*50}")
    print(f"  R2 Score : {r2:.4f}  ({r2*100:.1f}% variance explained)")
    print(f"  RMSE     : Rs {rmse/1e5:.2f} L  (Rs {rmse/1e7:.2f} Cr)")
    print(f"  MAE      : Rs {mae/1e5:.2f} L  (Rs {mae/1e7:.2f} Cr)")
    print(f"{'='*50}\n")

    importance = pd.Series(model.feature_importances_, index=FEATURES)
    print("  Feature Importances:")
    print(importance.sort_values(ascending=False).to_string())

    # ── Save ──────────────────────────────────────────────────────────────────
    with open(MODEL_PATH,   'wb') as f: pickle.dump(model,    f)
    with open(ENCODER_PATH, 'wb') as f: pickle.dump(encoders, f)
    print(f"\n[SAVED] {MODEL_PATH}")
    print(f"[SAVED] {ENCODER_PATH}")

    return model, encoders, df, {
        'r2':   round(r2,   4),
        'rmse': round(rmse, 2),
        'mae':  round(mae,  2),
    }


if __name__ == '__main__':
    train()
