# FairSquare | India's Real Estate Value & Deal Finder

FairSquare is an end-to-end Machine Learning project designed to identify underpriced residential properties across tier-1 and tier-2 Indian metropolitan markets (Mumbai, Delhi-NCR, Bengaluru, Pune, Hyderabad, Chennai, and Kolkata). 

By analyzing historical transaction patterns, the model calculates the **Fair Market Value (FMV)**—the mathematical "average predictable price"—of a listing based on structural and geographic parameters. By measuring the variance between the model's predicted FMV and the seller's actual listing price, FairSquare instantly flags and ranks potential investment deals.

---

## 🏗️ Project Architecture & Pipeline

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

## 🛠️ Tech Stack & Dependencies

The project is built entirely on a modern, decoupled Python-based Data Science stack:

*   **Python (v3.10+)**: Core programming environment providing high numerical computing capabilities.
*   **Pandas & NumPy**: Utilized for structural vectorization, cross-table indexing, structural cleaning, and matrix transformation of the raw listings dataset.
*   **Scikit-Learn**: The backbone of the machine learning pipeline. Used for dataset splits (`train_test_split`), numerical scaling, evaluation metrics, and running basic regressors.
*   **XGBoost & LightGBM**: Advanced gradient-boosted decision tree libraries deployed to isolate complex, non-linear relationships across nested geographical tiers.
*   **Matplotlib & Seaborn**: Deployed for generating residual error plots, spatial price heatmaps, and feature importance matrices.

---

## 📋 Prerequisites & Local Development Setup

### Why We Use a Virtual Environment (`venv`)
Python installations share global libraries by default. Running multiple projects globally can lead to *dependency hell*, where upgrading a library for Project A breaks Project B. 
A virtual environment creates an **isolated sandbox directory**. It maintains a local copy of the Python executable and packages inside the project root, ensuring exact reproducibility without polluting system-wide paths.

### 📥 Project Setup Step-by-Step

**Clone the Repository:**
   
```
   git clone [https://github.com/yourusername/FairSquare.git](https://github.com/yourusername/FairSquare.git)
   cd FairSquare
```

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
