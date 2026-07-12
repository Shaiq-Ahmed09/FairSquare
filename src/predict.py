"""
predict.py
----------
Loads the trained model, predicts FMV across all three merged datasets,
computes Deal Scores, and exports deals.json for the dashboard.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd

from preprocess import preprocess

# ── Paths ─────────────────────────────────────────────────────────────────────
V21_PATH     = 'dataset/Real Estate Data V21.csv'
DELHI_PATH   = 'dataset/Delhi_v2.csv'
PUNE_PATH    = 'dataset/pune_house_prices.csv'
KOLKATA_PATH = 'dataset/Kolkata_real_estate.csv'
MODEL_PATH   = 'models/fmv_model.pkl'
ENCODER_PATH = 'models/encoders.pkl'
OUTPUT_PATH  = 'dashboard/deals.json'

FEATURES = [
    'Total_Area', 'BHK', 'Baths', 'Balcony_Enc',
    'Price_per_SQFT', 'City_Enc', 'Property_Type_Enc', 'Source_Enc',
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def tag_deal(pct: float) -> str:
    if pct >= 20:  return 'Hot Deal'
    if pct >= 10:  return 'Good Deal'
    if pct >= 0:   return 'Fair Price'
    if pct >= -15: return 'Slightly Overpriced'
    return 'Overpriced'


def fmt_inr(v: float) -> str:
    if v >= 1e7:  return f'Rs {v/1e7:.2f} Cr'
    if v >= 1e5:  return f'Rs {v/1e5:.2f} L'
    return f'Rs {v:,.0f}'


def safe_encode(le, series: pd.Series) -> pd.Series:
    known = set(le.classes_)
    fallback = le.classes_[0]
    return le.transform(series.apply(lambda x: x if x in known else fallback))


# ── Main ──────────────────────────────────────────────────────────────────────

def predict_and_export(
    v21_path=V21_PATH, delhi_path=DELHI_PATH, pune_path=PUNE_PATH,
    kolkata_path=KOLKATA_PATH,
    model_path=MODEL_PATH, encoder_path=ENCODER_PATH,
    output_path=OUTPUT_PATH, metrics=None,
):
    os.makedirs('dashboard', exist_ok=True)

    # ── Load model ─────────────────────────────────────────────────────────────
    print("[1/5] Loading model & encoders...")
    with open(model_path,   'rb') as f: model    = pickle.load(f)
    with open(encoder_path, 'rb') as f: encoders = pickle.load(f)

    # ── Preprocess ─────────────────────────────────────────────────────────────
    print("[2/5] Preprocessing merged dataset...")
    df = preprocess(v21_path, delhi_path, pune_path, kolkata_path)

    # ── Encode ────────────────────────────────────────────────────────────────
    print("[3/5] Encoding categoricals...")
    df['City_Enc']          = safe_encode(encoders['city'],          df['City'])
    df['Property_Type_Enc'] = safe_encode(encoders['property_type'], df['Property_Type'])
    df['Source_Enc']        = safe_encode(encoders['source'],        df['Source'])

    # ── Predict ────────────────────────────────────────────────────────────────
    print("[4/5] Predicting Fair Market Values...")
    df['Predicted_FMV'] = model.predict(df[FEATURES])
    df['Deal_Score']    = df['Predicted_FMV'] - df['Price_INR']
    df['Deal_Pct']      = (df['Deal_Score'] / df['Price_INR']) * 100
    df['Deal_Tag']      = df['Deal_Pct'].apply(tag_deal)

    df = df.sort_values('Deal_Pct', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1

    # ── Summary stats ──────────────────────────────────────────────────────────
    total      = len(df)
    hot        = int((df['Deal_Tag'] == 'Hot Deal').sum())
    good       = int((df['Deal_Tag'] == 'Good Deal').sum())
    fair       = int((df['Deal_Tag'] == 'Fair Price').sum())
    overpriced = int(df['Deal_Tag'].str.contains('Overpriced').sum())

    # City chart
    city_stats = (
        df.groupby('City')
          .agg(avg_deal_pct=('Deal_Pct','mean'), count=('City','count'),
               avg_price=('Price_INR','mean'), avg_fmv=('Predicted_FMV','mean'))
          .reset_index().sort_values('avg_deal_pct', ascending=False)
    )

    # Source breakdown
    source_stats = df.groupby('Source').agg(
        count=('Source','count'),
        hot_deals=('Deal_Tag', lambda x: (x=='Hot Deal').sum()),
        avg_deal_pct=('Deal_Pct','mean'),
    ).reset_index()

    # Distribution bins
    bins   = [-200, -15, 0, 10, 20, 500]
    labels = ['Overpriced', 'Slightly Overpriced', 'Fair Price', 'Good Deal', 'Hot Deal']
    df['_bin'] = pd.cut(df['Deal_Pct'], bins=bins, labels=labels)
    dist = df['_bin'].value_counts().reindex(labels, fill_value=0).to_dict()

    # Scatter sample (1200 pts)
    sample = df.sample(min(1200, total), random_state=42)
    scatter = [
        {'actual': round(float(r.Price_INR), 0),
         'fmv':    round(float(r.Predicted_FMV), 0),
         'deal_pct': round(float(r.Deal_Pct), 1),
         'tag':    r.Deal_Tag, 'city': r.City, 'source': r.Source}
        for r in sample.itertuples()
    ]

    # ── Build listing records ──────────────────────────────────────────────────
    print("[5/5] Building JSON output...")
    records = []
    for r in df.itertuples():
        records.append({
            'rank':              int(r.Rank),
            'name':              str(r.Name)[:80],
            'title':             f"{int(r.BHK)} BHK {r.Property_Type} in {r.City}",
            'location':          str(r.Location)[:100],
            'city':              str(r.City),
            'source':            str(r.Source),
            'bhk':               int(r.BHK),
            'baths':             int(r.Baths),
            'balcony':           'Yes' if r.Balcony_Enc else 'No',
            'property_type':     str(r.Property_Type),
            'total_area':        round(float(r.Total_Area), 0),
            'price_per_sqft':    round(float(r.Price_per_SQFT), 0),
            'actual_price':      round(float(r.Price_INR), 0),
            'predicted_fmv':     round(float(r.Predicted_FMV), 0),
            'deal_score':        round(float(r.Deal_Score), 0),
            'deal_pct':          round(float(r.Deal_Pct), 2),
            'deal_tag':          str(r.Deal_Tag),
            'actual_price_fmt':  fmt_inr(r.Price_INR),
            'predicted_fmv_fmt': fmt_inr(r.Predicted_FMV),
            'deal_score_fmt':    fmt_inr(abs(r.Deal_Score)),
        })

    output = {
        'meta': {
            'total_listings':  total,
            'hot_deals':       hot,
            'good_deals':      good,
            'fair_price':      fair,
            'overpriced':      overpriced,
            'avg_deal_pct':    round(float(df['Deal_Pct'].mean()), 2),
            'model_r2':        metrics.get('r2', 0) if metrics else 0,
            'model_rmse_l':    round(metrics.get('rmse', 0)/1e5, 2) if metrics else 0,
            'cities':          sorted(df['City'].unique().tolist()),
            'property_types':  sorted(df['Property_Type'].unique().tolist()),
            'sources':         sorted(df['Source'].unique().tolist()),
        },
        'distribution':  dist,
        'city_chart':    city_stats.to_dict(orient='records'),
        'source_stats':  source_stats.to_dict(orient='records'),
        'scatter':       scatter,
        'listings':      records,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"  DEAL FINDER RESULTS")
    print(f"{'='*50}")
    print(f"  Total Listings : {total:,}")
    print(f"  Hot Deals      : {hot:,}")
    print(f"  Good Deals     : {good:,}")
    print(f"  Fair Price     : {fair:,}")
    print(f"  Overpriced     : {overpriced:,}")
    print(f"  Avg Deal Score : {df['Deal_Pct'].mean():+.1f}%")
    print(f"  Sources: {source_stats.set_index('Source')['count'].to_dict()}")
    print(f"{'='*50}")
    print(f"\n[SAVED] {output_path}")
    return output


if __name__ == '__main__':
    predict_and_export()
