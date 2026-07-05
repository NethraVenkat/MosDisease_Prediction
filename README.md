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
