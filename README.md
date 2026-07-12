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
