"""
preprocess.py
-------------
Cleans, normalises and merges three Indian real estate datasets:
  1. Real Estate Data V21.csv  (Chennai / multi-city, scraped listings)
  2. Delhi_v2.csv              (Delhi NCR listings)
  3. pune_house_prices.csv     (Pune listings)

Outputs a unified DataFrame with consistent columns ready for model training.

Unified schema (output columns):
  Price_INR        – numeric price in INR
  Total_Area       – sq ft (numeric)
  Price_per_SQFT   – INR / sqft (numeric)
  BHK              – integer bedrooms
  Baths            – integer bathrooms
  Balcony_Enc      – 0/1
  City             – normalised city name string
  Property_Type    – Flat / Villa / Independent House / Plot / Other
  Source           – origin dataset tag (Chennai/Delhi/Pune)
"""

import re
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# Shared utilities
# ──────────────────────────────────────────────────────────────────────────────

def remove_outliers_iqr(df: pd.DataFrame, col: str, k: float = 3.0) -> pd.DataFrame:
    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    iqr = q3 - q1
    return df[(df[col] >= q1 - k * iqr) & (df[col] <= q3 + k * iqr)]


def encode_balcony(val) -> int:
    if pd.isna(val):
        return 0
    return 1 if str(val).strip().lower() in ('yes', '1', 'true') else 0


PROPERTY_TYPE_RULES = [
    ('Villa',             r'villa'),
    ('Independent House', r'independent\s*house|builder\s*floor|kothi|bungalow|row\s*house'),
    ('Flat',              r'flat|apartment'),
    ('Plot',              r'plot|land'),
    ('Penthouse',         r'penthouse'),
    ('Studio',            r'studio'),
]

def classify_type(text: str) -> str:
    if pd.isna(text):
        return 'Other'
    t = str(text).lower()
    for label, pattern in PROPERTY_TYPE_RULES:
        if re.search(pattern, t):
            return label
    return 'Other'


# ──────────────────────────────────────────────────────────────────────────────
# Dataset 1 — Real Estate Data V21  (Chennai / multi-city)
# ──────────────────────────────────────────────────────────────────────────────

KNOWN_CITIES = {
    'mumbai': 'Mumbai', 'delhi': 'Delhi', 'bangalore': 'Bangalore',
    'bengaluru': 'Bangalore', 'chennai': 'Chennai', 'hyderabad': 'Hyderabad',
    'pune': 'Pune', 'kolkata': 'Kolkata', 'ahmedabad': 'Ahmedabad',
    'noida': 'Noida', 'gurgaon': 'Gurgaon', 'gurugram': 'Gurgaon',
    'thane': 'Thane', 'navi mumbai': 'Navi Mumbai', 'coimbatore': 'Coimbatore',
    'kochi': 'Kochi', 'jaipur': 'Jaipur', 'lucknow': 'Lucknow',
}

def _extract_city_v21(loc: str) -> str:
    if pd.isna(loc):
        return 'Unknown'
    loc_lower = loc.lower()
    for key, val in KNOWN_CITIES.items():
        if key in loc_lower:
            return val
    parts = [p.strip() for p in loc.split(',')]
    return parts[-1].strip() if parts else 'Unknown'


def _parse_price_v21(price_str) -> float:
    if pd.isna(price_str):
        return np.nan
    s = str(price_str).replace('₹', '').replace(',', '').strip()
    try:
        if 'Cr' in s:
            return float(re.sub(r'[^\d.]', '', s.replace('Cr', ''))) * 1e7
        if 'L' in s:
            return float(re.sub(r'[^\d.]', '', s.replace('L', '')))  * 1e5
        return float(re.sub(r'[^\d.]', '', s))
    except Exception:
        return np.nan


def load_v21(path: str) -> pd.DataFrame:
    print(f"  [V21] Loading: {path}")
    df = pd.read_csv(path, encoding='utf-8-sig')
    print(f"  [V21] Raw rows: {len(df)}")

    out = pd.DataFrame()
    out['Price_INR']      = df['Price'].apply(_parse_price_v21)
    out['Total_Area']     = pd.to_numeric(df['Total_Area'],     errors='coerce')
    out['Price_per_SQFT'] = pd.to_numeric(df['Price_per_SQFT'], errors='coerce')
    out['Baths']          = pd.to_numeric(df['Baths'],          errors='coerce')
    out['Balcony_Enc']    = df['Balcony'].apply(encode_balcony)
    out['City']           = df['Location'].apply(_extract_city_v21)

    # BHK from Property Title
    out['BHK'] = df['Property Title'].apply(
        lambda t: int(m.group(1)) if (m := re.search(r'(\d+)\s*BHK', str(t), re.I)) else np.nan
    )
    # Property type from title
    out['Property_Type'] = df['Property Title'].apply(classify_type)
    out['Source'] = 'Chennai/Multi'

    # Keep raw name for display
    out['Name']     = df.get('Name', '').fillna('')
    out['Location'] = df.get('Location', '').fillna('')

    return out


# ──────────────────────────────────────────────────────────────────────────────
# Dataset 2 — Delhi_v2.csv
# ──────────────────────────────────────────────────────────────────────────────

def _extract_city_delhi(address: str) -> str:
    if pd.isna(address):
        return 'Delhi'
    addr = address.lower()
    if 'gurgaon' in addr or 'gurugram' in addr:
        return 'Gurgaon'
    if 'noida' in addr or 'greater noida' in addr:
        return 'Noida'
    if 'faridabad' in addr:
        return 'Faridabad'
    if 'ghaziabad' in addr:
        return 'Ghaziabad'
    return 'Delhi'


def load_delhi(path: str) -> pd.DataFrame:
    print(f"  [Delhi] Loading: {path}")
    # Delhi CSV has multiline descriptions embedded — read carefully
    df = pd.read_csv(
        path,
        encoding='utf-8-sig',
        on_bad_lines='skip',
        engine='python',
        quotechar='"',
    )
    print(f"  [Delhi] Raw rows: {len(df)}")

    out = pd.DataFrame()
    out['Price_INR']      = pd.to_numeric(df['price'],      errors='coerce')
    out['Total_Area']     = pd.to_numeric(df['area'],       errors='coerce')
    out['Price_per_SQFT'] = pd.to_numeric(df['Price_sqft'], errors='coerce')
    out['BHK']            = pd.to_numeric(df['Bedrooms'],   errors='coerce')
    out['Baths']          = pd.to_numeric(df['Bathrooms'],  errors='coerce')
    out['Balcony_Enc']    = df['Balcony'].apply(encode_balcony)
    out['City']           = df['Address'].apply(_extract_city_delhi)
    out['Property_Type']  = df['type_of_building'].apply(classify_type)
    out['Source']         = 'Delhi'

    # Derive missing Price_per_SQFT
    mask = out['Price_per_SQFT'].isna() & out['Total_Area'].gt(0)
    out.loc[mask, 'Price_per_SQFT'] = (
        out.loc[mask, 'Price_INR'] / out.loc[mask, 'Total_Area']
    )

    out['Name']     = df.get('Address', '').fillna('').astype(str)
    out['Location'] = df.get('Address', '').fillna('').astype(str)

    return out


# ──────────────────────────────────────────────────────────────────────────────
# Dataset 3 — pune_house_prices.csv
# ──────────────────────────────────────────────────────────────────────────────

def load_pune(path: str) -> pd.DataFrame:
    print(f"  [Pune] Loading: {path}")
    df = pd.read_csv(path, encoding='utf-8-sig')
    print(f"  [Pune] Raw rows: {len(df)}")

    out = pd.DataFrame()
    out['Price_INR']   = pd.to_numeric(df['price'],         errors='coerce')
    out['Total_Area']  = pd.to_numeric(df['square_feet'],   errors='coerce')
    out['BHK']         = pd.to_numeric(df['num_bedrooms'],  errors='coerce')
    out['Baths']       = pd.to_numeric(df['num_bathrooms'], errors='coerce')
    # Pune dataset: has_garage → treat as balcony proxy (0/1 already)
    out['Balcony_Enc'] = pd.to_numeric(df.get('has_garage', 0), errors='coerce').fillna(0).astype(int)
    out['City']        = 'Pune'
    out['Property_Type'] = 'Flat'   # Pune dataset is all apartments

    # Derive Price_per_SQFT
    out['Price_per_SQFT'] = np.where(
        out['Total_Area'] > 0,
        out['Price_INR'] / out['Total_Area'],
        np.nan
    )

    out['Source']   = 'Pune'
    out['Name']     = df.get('area', '').fillna('').astype(str)
    out['Location'] = df.get('area', '').fillna('').astype(str) + ', Pune'

    return out


# ──────────────────────────────────────────────────────────────────────────────
# Dataset 4 — Kolkata_real_estate.csv
# ──────────────────────────────────────────────────────────────────────────────

def _parse_price_kolkata(price_str) -> float:
    """Parse Indian price strings: '₹2.38 Cr', '₹32 Lac', '₹50 Lac'"""
    if pd.isna(price_str):
        return np.nan
    s = str(price_str).replace('₹', '').replace(',', '').strip()
    try:
        if 'Cr' in s:
            return float(re.sub(r'[^\d.]', '', s.replace('Cr', ''))) * 1e7
        if 'Lac' in s or 'L' in s:
            num_str = re.sub(r'[^\d.]', '', re.sub(r'Lac|L', '', s))
            return float(num_str) * 1e5
        return float(re.sub(r'[^\d.]', '', s))
    except Exception:
        return np.nan


def _parse_area_kolkata(area_str) -> float:
    """Parse '1850 sqft' -> 1850.0"""
    if pd.isna(area_str):
        return np.nan
    try:
        return float(re.sub(r'[^\d.]', '', str(area_str)))
    except Exception:
        return np.nan


def load_kolkata(path: str) -> pd.DataFrame:
    print(f"  [Kolkata] Loading: {path}")
    df = pd.read_csv(path, encoding='utf-8-sig')
    print(f"  [Kolkata] Raw rows: {len(df)}")

    out = pd.DataFrame()
    out['Price_INR']  = df['Price'].apply(_parse_price_kolkata)
    out['Total_Area'] = df['Area'].apply(_parse_area_kolkata)
    out['City']       = 'Kolkata'
    out['Source']     = 'Kolkata'

    # BHK from Name column (e.g. '4 BHK Apartment for Sale in ...')
    out['BHK'] = df['Name'].apply(
        lambda t: int(m.group(1)) if (m := re.search(r'(\d+)\s*BHK', str(t), re.I)) else np.nan
    )
    out['Property_Type'] = df['Name'].apply(classify_type)

    # Kolkata dataset has no Bathrooms column — estimate from BHK
    out['Baths']      = out['BHK'].fillna(2).clip(upper=6)
    out['Balcony_Enc'] = 0  # not available

    # Derive Price_per_SQFT
    out['Price_per_SQFT'] = np.where(
        out['Total_Area'] > 0,
        out['Price_INR'] / out['Total_Area'],
        np.nan
    )

    # Furnishing as a proxy for balcony
    if 'Furnishing' in df.columns:
        out['Balcony_Enc'] = df['Furnishing'].apply(
            lambda x: 1 if str(x).strip().lower() in ('semi-furnished', 'furnished') else 0
        )

    out['Name']     = df['Name'].fillna('').astype(str)
    out['Location'] = df['Name'].fillna('').astype(str) + ', Kolkata'

    return out


# ──────────────────────────────────────────────────────────────────────────────
# Main merge + clean
# ──────────────────────────────────────────────────────────────────────────────

def preprocess(
    v21_path:     str = 'dataset/Real Estate Data V21.csv',
    delhi_path:   str = 'dataset/Delhi_v2.csv',
    pune_path:    str = 'dataset/pune_house_prices.csv',
    kolkata_path: str = 'dataset/Kolkata_real_estate.csv',
) -> pd.DataFrame:
    """
    Load all three datasets, normalise to a unified schema,
    clean and return a merged DataFrame.
    """
    print("[1/5] Loading datasets...")
    dfs = []

    try:
        dfs.append(load_v21(v21_path))
        print(f"       V21 loaded: {len(dfs[-1])} rows")
    except Exception as e:
        print(f"       V21 SKIPPED: {e}")

    try:
        dfs.append(load_delhi(delhi_path))
        print(f"       Delhi loaded: {len(dfs[-1])} rows")
    except Exception as e:
        print(f"       Delhi SKIPPED: {e}")

    try:
        dfs.append(load_pune(pune_path))
        print(f"       Pune loaded: {len(dfs[-1])} rows")
    except Exception as e:
        print(f"       Pune SKIPPED: {e}")

    try:
        dfs.append(load_kolkata(kolkata_path))
        print(f"       Kolkata loaded: {len(dfs[-1])} rows")
    except Exception as e:
        print(f"       Kolkata SKIPPED: {e}")

    print(f"\n[2/5] Merging {len(dfs)} datasets...")
    df = pd.concat(dfs, ignore_index=True)
    print(f"      Combined rows: {len(df)}")

    # ── Numeric coercion ──────────────────────────────────────
    print("[3/5] Coercing types...")
    for col in ['Price_INR', 'Total_Area', 'Price_per_SQFT', 'BHK', 'Baths']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ── Drop rows missing critical columns ────────────────────
    print("[4/5] Dropping nulls and outliers...")
    critical = ['Price_INR', 'Total_Area', 'BHK', 'Baths']
    before = len(df)
    df = df.dropna(subset=critical)
    print(f"      Dropped {before - len(df)} rows with null critical fields")

    # ── Fill derived Price_per_SQFT if still missing ──────────
    mask = df['Price_per_SQFT'].isna() & (df['Total_Area'] > 0)
    df.loc[mask, 'Price_per_SQFT'] = df.loc[mask, 'Price_INR'] / df.loc[mask, 'Total_Area']
    df = df.dropna(subset=['Price_per_SQFT'])

    # ── Cap BHK at 8 ─────────────────────────────────────────
    df['BHK']   = df['BHK'].clip(upper=8)
    df['Baths'] = df['Baths'].clip(upper=10)

    # ── Minimum area / price sanity ───────────────────────────
    df = df[df['Total_Area'] >= 100]      # sqft: nothing below 100
    df = df[df['Price_INR']  >= 200_000]  # ₹2L minimum
    df = df[df['BHK']        >= 1]
    df = df[df['Baths']      >= 1]

    # ── IQR outlier removal per source so one dataset doesn't
    #    skew the others ────────────────────────────────────────
    cleaned = []
    for src, grp in df.groupby('Source'):
        n_before = len(grp)
        grp = remove_outliers_iqr(grp, 'Price_INR',      k=3.0)
        grp = remove_outliers_iqr(grp, 'Total_Area',     k=3.0)
        grp = remove_outliers_iqr(grp, 'Price_per_SQFT', k=3.0)
        print(f"      [{src}] {n_before} → {len(grp)} rows after outlier removal")
        cleaned.append(grp)

    df = pd.concat(cleaned, ignore_index=True)

    # ── Normalise BHK/Baths to int ────────────────────────────
    df['BHK']       = df['BHK'].round().astype(int)
    df['Baths']     = df['Baths'].round().astype(int)
    df['Balcony_Enc'] = df['Balcony_Enc'].fillna(0).astype(int)

    # ── Fill blanks ───────────────────────────────────────────
    df['Name']     = df['Name'].fillna('').astype(str)
    df['Location'] = df['Location'].fillna('').astype(str)

    print(f"\n[5/5] Final dataset: {len(df)} rows")
    print(f"      Cities: {sorted(df['City'].unique())}")
    print(f"      Sources: {df.groupby('Source').size().to_dict()}")
    print(f"      Property types: {sorted(df['Property_Type'].unique())}")

    return df


if __name__ == '__main__':
    df = preprocess()
    print(df[['Source','City','BHK','Price_INR','Total_Area','Price_per_SQFT','Property_Type']].head(10))
