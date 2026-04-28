# Disease Outbreak Hotspot Predictor
### with Digital Twin Simulation and Explainable AI

A production-ready Python system that:
- Trains a RandomForest ML model on the Dengue Features and Outcomes dataset
- Predicts disease outbreak risk (Low / Medium / High)
- Finds historically similar records and generates AI-driven explanations
- Runs Digital Twin simulations to model what-if environmental scenarios
- Stores all outputs in MongoDB
- Exposes everything through a clean FastAPI REST API

---

## Project Structure

```
disease_predictor_project/
├── data/
│   └── dengue.csv              ← Place your Kaggle dataset here
├── model/
│   ├── train_model.py          ← Training script
│   └── model.pkl               ← Generated after training
├── backend/
│   ├── config.py               ← MongoDB URI and paths
│   ├── db.py                   ← PyMongo CRUD operations
│   └── main.py                 ← FastAPI application
├── similarity/
│   └── similarity.py           ← Explainable AI / KNN similarity
├── simulation/
│   └── simulate.py             ← Digital Twin simulation engine
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone / Download the project

```bash
# Navigate into the project folder
cd disease_predictor_project
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your dataset

- Download the **Dengue Features and Outcomes** dataset from Kaggle
- Rename the file to `dengue.csv`
- Place it inside the `data/` folder:

```
disease_predictor_project/data/dengue.csv
```

### 5. Configure MongoDB

Open `backend/config.py` and replace the placeholder with your real connection string:

```python
MONGO_URI = "mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority"
```

### 5b. Configure SMS alerts (optional)

To send SMS when risk is **Medium** or **High**, set these environment variables:

Option A (recommended): create a `.env` file in project root from `.env.example`.

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set your real values.

Option B: set temporary PowerShell environment variables:

```powershell
$env:SMS_ENABLED="true"
$env:SMS_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:SMS_AUTH_TOKEN="your_twilio_auth_token"
$env:SMS_FROM_NUMBER="+1xxxxxxxxxx"
$env:SMS_TO_NUMBER="+91xxxxxxxxxx"
```

Notes:
- Uses Twilio REST API from backend.
- SMS is triggered for `/predict` and `/simulate` when predicted/simulated risk is Medium or High.
- Response includes `sms_alert` status (`sent`, `reason`).

### 6. Train the model

Run this from the **project root** (the folder containing `data/`, `model/`, `backend/`, etc.):

```bash
python -m model.train_model
```

You will see accuracy metrics and a confirmation that `model/model.pkl` was saved.

### 7. Start the API server

```bash
uvicorn backend.main:app --reload
```

The API will be live at: **http://127.0.0.1:8000**

Interactive docs: **http://127.0.0.1:8000/docs**

---

## API Reference

### GET `/`
Health check — confirms the API is running.

---

### POST `/predict`
Predict outbreak risk for a given set of environmental conditions.

**Request body:**
```json
{
  "features": {
    "station_avg_temp_c": 28.5,
    "precipitation_amt_mm": 120.0,
    "reanalysis_relative_humidity_percent": 78.0
  }
}
```

> Use the exact column names from your dengue.csv file as keys.

**Response:**
```json
{
  "predicted_risk": "High",
  "probability": 0.87,
  "similarity_insight": "Analysis of 3 historically similar case(s) revealed: ...",
  "similar_records": [...],
  "sms_alert": {
    "enabled": true,
    "sent": true,
    "reason": "ok"
  }
}
```

---

### POST `/simulate`
Digital Twin simulation — modify environmental parameters and compare real vs simulated risk.

**Request body:**
```json
{
  "features": {
    "station_avg_temp_c": 28.5,
    "precipitation_amt_mm": 120.0,
    "reanalysis_relative_humidity_percent": 78.0
  },
  "rainfall_delta": 30,
  "humidity_delta": 15,
  "temperature_delta": 0
}
```

> `rainfall_delta: 30` means "increase rainfall features by 30%".

**Response:**
```json
{
  "real_risk": "Medium",
  "simulated_risk": "High",
  "simulated_probability": 0.91,
  "delta_summary": "Simulation applied: [...]. Outbreak risk changed from Medium → High.",
  "similarity_insight": "...",
  "simulated_input": {...},
  "sms_alert": {
    "enabled": true,
    "sent": true,
    "reason": "ok"
  }
}
```

---

### GET `/history`
Returns all stored records from MongoDB.

```json
{
  "total": 42,
  "records": [...]
}
```

---

### GET `/high-risk`
Returns only records where `predicted_risk` is `"High"`.

```json
{
  "total_high_risk": 7,
  "records": [...]
}
```

---

## How It Works

### Machine Learning
- Algorithm: `RandomForestClassifier` (200 trees, max depth 10)
- Target: auto-detected cases column → converted to Low / Medium / High labels using 33rd/66th percentile thresholds
- Features: all numeric columns in the CSV except the target

### Explainable AI (Similarity Analysis)
- Normalises all features using Min-Max scaling
- Computes Euclidean distance between user input and every row in the dataset
- Returns the 3 closest historical records
- Generates a human-readable insight string explaining what conditions are associated with the predicted risk

### Digital Twin Simulation
- Copies the original input
- Applies percentage changes to rainfall, humidity, and/or temperature columns (matched by keyword)
- Runs the model on the modified input
- Returns a side-by-side comparison of real vs simulated risk

### MongoDB Storage
- All prediction and simulation outputs are stored in the `disease_db.predictions` collection
- The raw CSV dataset is never stored in MongoDB

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Model file not found` | Run `python -m model.train_model` first |
| `Dataset not found` | Place `dengue.csv` in the `data/` folder |
| `MongoDB connection failed` | Check your `MONGO_URI` in `backend/config.py` |
| `No numeric feature columns found` | Ensure your CSV has numeric columns beside the cases column |

---

## Viva Questions

1. **What is a Digital Twin in the context of disease prediction?**
   A Digital Twin is a virtual replica of a real-world system (here, an environmental location) that allows you to simulate "what-if" scenarios—for example, what happens to outbreak risk if rainfall increases by 30%—without any real-world consequences.

2. **Why is RandomForest chosen over a simpler model like Logistic Regression?**
   RandomForest handles non-linear relationships between environmental variables and outbreak risk, is robust to outliers and missing data, provides feature importance rankings, and generally achieves higher accuracy on tabular datasets with relatively little hyperparameter tuning.

3. **How does the Explainable AI module make the model's predictions understandable?**
   Instead of presenting a black-box output, the similarity module finds the 3 most historically similar records from real data (using Euclidean distance on normalised features) and generates a plain-English explanation of what environmental conditions were associated with those past outbreaks.

4. **Why are risk labels derived from percentiles rather than fixed absolute case numbers?**
   Different geographic regions and time periods have very different baseline case counts. Percentile-based thresholds (33rd / 66th percentile) automatically adapt to the actual distribution of the dataset, ensuring balanced class representation across Low, Medium, and High categories.

5. **What is the purpose of Min-Max normalisation in the similarity analysis?**
   Features like temperature (20-35°C), rainfall (0-300 mm), and humidity (40-100%) have completely different numerical scales. Without normalisation, high-magnitude features (like rainfall) would dominate the Euclidean distance calculation, making the similarity search biased toward those features and ignoring lower-scale but equally important ones.

---

## Interview Questions

1. **How would you scale this system to handle predictions for thousands of cities simultaneously?**
   The FastAPI app is already stateless (model loaded once at startup), making it horizontally scalable behind a load balancer. MongoDB can be sharded by city/region. For batch inference across thousands of locations, the prediction logic can be extracted into an async worker queue (e.g., Celery + Redis) that processes inputs in parallel, with results streamed back via WebSockets or stored for polling.

2. **What steps would you take to improve model accuracy if the current F1-score is below 80%?**
   First, perform feature engineering—lag features (cases from previous weeks), rolling averages, and cross-features (e.g., humidity × temperature). Second, tune hyperparameters using RandomizedSearchCV. Third, try gradient boosting models (XGBoost, LightGBM) and ensemble them with RandomForest. Fourth, address class imbalance using SMOTE or class_weight='balanced'. Finally, incorporate external data (satellite imagery, population density, healthcare infrastructure).

3. **How does storing only outputs (not the dataset) in MongoDB align with data engineering best practices?**
   It follows the principle of separation of concerns: the raw dataset is a static analytical artifact best stored in flat files or a data lake (S3, GCS), while MongoDB is optimised for storing operational, timestamped prediction records that the API queries frequently. This avoids data duplication, keeps the MongoDB collection lean and fast to query, and prevents the operational database from becoming a bottleneck when the dataset grows to millions of rows.
