# FairSquare | India's Real Estate Value & Deal Finder

FairSquare is an end-to-end Machine Learning project designed to identify underpriced residential properties across tier-1 and tier-2 Indian metropolitan markets (Mumbai, Delhi-NCR, Bengaluru, Pune, Hyderabad, Chennai, and Kolkata). 

By analyzing historical transaction patterns, the model calculates the **Fair Market Value (FMV)**—the mathematical "average predictable price"—of a listing based on structural and geographic parameters. By measuring the variance between the model's predicted FMV and the seller's actual listing price, FairSquare instantly flags and ranks potential investment deals.

---

## Project Architecture & Pipeline

[ Raw Indian Real Estate Data (CSV) ]
│
▼
[ Data Standardization ] ──► (Converts mixed string 'Cr'/'Lac' to raw INR integers)
│
▼
[ Preprocessing & EDA ]  ──► (Handles missing values, caps outliers using IQR)
│
▼
[ Feature Engineering ]  ──► (Target Encoding for Locality, extracts Super vs Carpet area metrics)
│
▼
[ Model Selection Loop ]  ──► (Evaluates Linear Regression vs Random Forest vs XGBoost)
│
▼
[ Variance Extraction ]  ──► (Deal Score = Predicted FMV - Actual Listing Price)
│
▼
[ Sorted Top Investment Opportunities Dashboard ]

---

## Tech Stack & Dependencies

The project is built entirely on a modern, decoupled Python-based Data Science stack:

*   **Python (v3.10+)**: Core programming environment providing high numerical computing capabilities.
*   **Pandas & NumPy**: Utilized for structural vectorization, cross-table indexing, structural cleaning, and matrix transformation of the raw listings dataset.
*   **Scikit-Learn**: The backbone of the machine learning pipeline. Used for dataset splits (`train_test_split`), numerical scaling, evaluation metrics, and running basic regressors.
*   **XGBoost & LightGBM**: Advanced gradient-boosted decision tree libraries deployed to isolate complex, non-linear relationships across nested geographical tiers.
*   **Matplotlib & Seaborn**: Deployed for generating residual error plots, spatial price heatmaps, and feature importance matrices.

---

## Prerequisites & Local Development Setup

### Why We Use a Virtual Environment (`venv`)
Python installations share global libraries by default. Running multiple projects globally can lead to *dependency hell*, where upgrading a library for Project A breaks Project B. 
A virtual environment creates an **isolated sandbox directory**. It maintains a local copy of the Python executable and packages inside the project root, ensuring exact reproducibility without polluting system-wide paths.


### Project Setup Step-by-Step

**Clone the Repository:**
   
```
git clone [https://github.com/yourusername/FairSquare.git](https://github.com/yourusername/FairSquare.git)
cd FairSquare
```

---

# Initialize a Virtual Environment:

**Windows:**
```
python -m venv venv
.\venv\Scripts\activate
```

**MacOS/Linux:**

```
python3 -m venv venv
source venv/bin/activate
```


**Install Core Dependencies:**
Ensure your local pip installer is updated, then compile the environment stack:

```
pip install --upgrade pip
pip install -r requirements.txt
```

---

# Core Machine Learning Methods Deployed

**1. Advanced Indian Preprocessing & Feature Engineering**

**Text Currency Normalization**: Web-scraped real estate parameters across Indian channels often concatenate text strings into numeric scales (e.g., ₹ 1.25 Cr vs ₹ 85 Lakh). A custom parser regex systematically transforms mixed scalar text elements into standardized numeric base values ($10,000,000 for Crore, $100,000 for Lakh).

**High-Cardinality Target Encoding**: The dataset spans thousands of regional micro-markets (Locality). One-Hot encoding would result in a massive, sparse matrix that introduces high variance. Instead, Target Encoding maps each locality categorical feature to the global expected mean of the target variable (Price per SqFt).

**Structural Discrepancy Multipliers**: Computes engineered features such as:
   Super-To-Carpet-Ratio = Super Built-Up Area/Carpet Area
   This captures the hidden overheads often bundled into high-rise society apartments versus independent builder floors.

**2. Supervised Learning Regression Models**

Because predicting real estate value is a continuous variable problem, the data is evaluated against three core architectures:

**Ordinary Least Squares (OLS) Linear Regression**: Serves as the basic linear baseline.

**Random Forest Regressor**: An ensemble bagger utilized to limit overfitting trends across highly fragmented feature nodes.

**XGBoost (Extreme Gradient Boosting)**: The ultimate production model deployed to handle complex multi-variate dependencies (e.g., the intersection of City, Furnishing Status, and BHK Type).

**3. Model Evaluation Metrics**

Models are scored and benchmarked utilizing:

**Mean Absolute Error (MAE)**: Expresses structural deviation errors directly in standard currency (INR Value), making performance easily interpretable for developers and real-world users.

**Root Mean Squared Logarithmic Error (RMSLE)**: Used to ensure that errors on premium luxury villas (e.g., a ₹15 Crore property in South Mumbai) don't disproportionately distort the loss function relative to standard middle-tier apartments.

---

# How to Run the Pipeline

1. Place your dataset (e.g., scraped Pan-India CSV files) inside the /data/raw/ directory.

2. Execute the complete data pipeline:
```
python src/main.py
```

3. To view detailed model diagnostics and visual residual error plots, spin up the interactive workspace:
```
jupyter notebook notebooks/exploratory_analysis.ipynb
```

---
