# main.py
# FastAPI backend for the Disease Outbreak Hotspot Predictor
# Run with: uvicorn backend.main:app --reload

import os
import sys
import pickle
import base64
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
from urllib import request as urllib_request
from urllib.parse import urlencode

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MosDisease_Prediction.backend.config import (
    MODEL_PATH,
    DATASET_PATH,
    SMS_ENABLED,
    SMS_ACCOUNT_SID,
    SMS_AUTH_TOKEN,
    SMS_FROM_NUMBER,
    SMS_TO_NUMBER,
)
from MosDisease_Prediction.backend.db import insert_prediction, fetch_all_predictions, fetch_high_risk_predictions
from MosDisease_Prediction.similarity.similarity import run_similarity_analysis
from MosDisease_Prediction.simulation.simulation import run_simulation

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Disease Outbreak Hotspot Predictor",
    description=(
        "Predicts dengue outbreak risk using ML, "
        "Explainable AI similarity analysis, and Digital Twin simulation."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

# ---------------------------------------------------------------------------
# Load model and dataset at startup
# ---------------------------------------------------------------------------
MODEL_BUNDLE: dict = {}
DATASET_DF: pd.DataFrame = pd.DataFrame()


@app.on_event("startup")
def startup_event():
    global MODEL_BUNDLE, DATASET_DF

    # Load model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Model file not found at '{MODEL_PATH}'. "
            "Please run: python -m model.train_model"
        )
    with open(MODEL_PATH, "rb") as f:
        MODEL_BUNDLE = pickle.load(f)
    print("[INFO] Model loaded successfully.")

    # Load dataset for similarity analysis
    if os.path.exists(DATASET_PATH):
        DATASET_DF = pd.read_csv(DATASET_PATH)
        print(f"[INFO] Dataset loaded: {DATASET_DF.shape[0]} rows.")
    else:
        print(f"[WARNING] Dataset not found at '{DATASET_PATH}'. Similarity analysis disabled.")


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    """Dynamic input: accepts any key-value pairs matching feature column names."""
    features: dict = Field(
        ...,
        example={
            "Year": 0,
            "Latitude": 0,
            "Longitude": 0,
            "Elevation": 0,
            "Month": 0,
            "Cases": 10,
            "Temp_avg": 30,
            "Precipitation_avg": 144,
        },
        description=(
            "A JSON object where keys are feature column names from dengue.csv "
            "and values are the corresponding numeric measurements."
        ),
    )


class SimulateRequest(BaseModel):
    """Request model for Digital Twin simulation."""
    features: dict = Field(
        ...,
        example={
            "Year": 0,
            "Latitude": 0,
            "Longitude": 0,
            "Elevation": 0,
            "Month": 0,
            "Cases": 10,
            "Temp_avg": 30,
            "Precipitation_avg": 144,
        },
        description="Original environmental feature values (same format as /predict).",
    )
    rainfall_delta: float = Field(
        default=0.0,
        description="Percentage change to apply to rainfall-related features (e.g., 20 = +20%).",
    )
    humidity_delta: float = Field(
        default=0.0,
        description="Percentage change to apply to humidity-related features.",
    )
    temperature_delta: float = Field(
        default=0.0,
        description="Percentage change to apply to temperature-related features.",
    )


# ---------------------------------------------------------------------------
# Helper: predict risk from a feature dict
# ---------------------------------------------------------------------------

def _predict_risk(features: dict) -> dict:
    """Run inference using the loaded RandomForest model."""
    clf = MODEL_BUNDLE["model"]
    le = MODEL_BUNDLE["label_encoder"]
    feature_cols = MODEL_BUNDLE["feature_cols"]

    # Build input vector; missing features default to 0
    input_vector = np.array([[features.get(c, 0.0) for c in feature_cols]])
    pred_encoded = clf.predict(input_vector)[0]
    proba = clf.predict_proba(input_vector)[0]

    risk_label = le.inverse_transform([pred_encoded])[0]
    probability = round(float(max(proba)), 4)

    return {"predicted_risk": risk_label, "probability": probability}


def _serve_frontend_file(filename: str):
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"Frontend file '{filename}' not found.")


def _should_send_sms(risk_level: str) -> bool:
    return str(risk_level).strip().lower() in {"medium", "high", "moderate"}


def _send_sms_alert(risk_level: str, source: str) -> dict:
    """Send SMS alert through Twilio for Medium/High risk levels."""
    normalized = str(risk_level).strip().lower()

    if not _should_send_sms(normalized):
        return {"enabled": SMS_ENABLED, "sent": False, "reason": "risk_below_threshold"}

    if not SMS_ENABLED:
        return {"enabled": False, "sent": False, "reason": "sms_disabled"}

    required_values = [SMS_ACCOUNT_SID, SMS_AUTH_TOKEN, SMS_FROM_NUMBER, SMS_TO_NUMBER]
    if not all(required_values):
        return {"enabled": True, "sent": False, "reason": "missing_sms_config"}

    level = "High" if normalized == "high" else "Medium"
    message_body = (
        f"Dengue Alert ({source}): {level} outbreak risk detected. "
        "Please take preventive action immediately."
    )

    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{SMS_ACCOUNT_SID}/Messages.json"
    payload = urlencode({
        "To": SMS_TO_NUMBER,
        "From": SMS_FROM_NUMBER,
        "Body": message_body,
    }).encode("utf-8")

    auth_raw = f"{SMS_ACCOUNT_SID}:{SMS_AUTH_TOKEN}".encode("utf-8")
    auth_header = base64.b64encode(auth_raw).decode("utf-8")

    req = urllib_request.Request(twilio_url, data=payload, method="POST")
    req.add_header("Authorization", f"Basic {auth_header}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            sent_ok = 200 <= status_code < 300
            return {
                "enabled": True,
                "sent": sent_ok,
                "reason": "ok" if sent_ok else f"http_{status_code}",
            }
    except Exception as exc:
        return {
            "enabled": True,
            "sent": False,
            "reason": "request_failed",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root():
    if os.path.isdir(FRONTEND_DIR):
        return _serve_frontend_file("index.html")
    return {
        "status": "running",
        "message": "Disease Outbreak Hotspot Predictor API is live.",
        "endpoints": ["/predict", "/simulate", "/history", "/high-risk"],
    }


@app.get("/dashboard", summary="Frontend dashboard page")
def dashboard_page():
    return _serve_frontend_file("dashboard.html")


@app.get("/solutions", summary="Frontend solutions page")
def solutions_page():
    return _serve_frontend_file("solutions.html")


@app.get("/health", summary="JSON health check")
def health():
    return {
        "status": "running",
        "message": "Disease Outbreak Hotspot Predictor API is live.",
    }


@app.get("/schema", summary="Return the model input schema")
def schema():
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    return {
        "feature_cols": MODEL_BUNDLE["feature_cols"],
        "target_col": MODEL_BUNDLE.get("target_col"),
    }


@app.post("/predict", summary="Predict outbreak risk and store result in MongoDB")
def predict(request: PredictRequest):
    """
    Accepts environmental feature values, predicts dengue outbreak risk,
    runs similarity-based Explainable AI, and stores the result in MongoDB.
    """
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    try:
        prediction = _predict_risk(request.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    # Similarity / Explainable AI
    similarity_insight = "Dataset not available for similarity analysis."
    similar_records = []
    if not DATASET_DF.empty:
        sim_result = run_similarity_analysis(
            df=DATASET_DF,
            input_values=request.features,
            feature_cols=MODEL_BUNDLE["feature_cols"],
            top_n=3,
        )
        similarity_insight = sim_result["insight"]
        similar_records = sim_result["similar_records"]

    # Build MongoDB document
    record = {
        **request.features,
        "predicted_risk": prediction["predicted_risk"],
        "probability": prediction["probability"],
        "similarity_insight": similarity_insight,
        "real_risk": prediction["predicted_risk"],
        "simulated_risk": None,
    }

    try:
        insert_prediction(record)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {str(e)}")

    sms_alert = _send_sms_alert(prediction["predicted_risk"], source="Prediction")

    return {
        "predicted_risk": prediction["predicted_risk"],
        "probability": prediction["probability"],
        "similarity_insight": similarity_insight,
        "similar_records": similar_records,
        "sms_alert": sms_alert,
    }


@app.post("/simulate", summary="Digital Twin simulation — vary environmental parameters")
def simulate(request: SimulateRequest):
    """
    Runs a Digital Twin simulation by modifying rainfall, humidity, or temperature
    by the given percentage deltas and comparing real vs simulated risk.
    Stores both real and simulated results in MongoDB.
    """
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    # First predict on the original (real) input
    try:
        real_prediction = _predict_risk(request.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real prediction error: {str(e)}")

    # Run simulation
    try:
        sim_result = run_simulation(
            model_bundle=MODEL_BUNDLE,
            original_input=request.features,
            rainfall_delta=request.rainfall_delta,
            humidity_delta=request.humidity_delta,
            temperature_delta=request.temperature_delta,
            original_risk=real_prediction["predicted_risk"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

    # Similarity insight for real input
    similarity_insight = "Dataset not available."
    if not DATASET_DF.empty:
        sim_analysis = run_similarity_analysis(
            df=DATASET_DF,
            input_values=request.features,
            feature_cols=MODEL_BUNDLE["feature_cols"],
            top_n=3,
        )
        similarity_insight = sim_analysis["insight"]

    # Build MongoDB document
    record = {
        **request.features,
        "predicted_risk": real_prediction["predicted_risk"],
        "probability": real_prediction["probability"],
        "similarity_insight": similarity_insight,
        "real_risk": sim_result["real_risk"],
        "simulated_risk": sim_result["simulated_risk"],
        "simulated_probability": sim_result["simulated_probability"],
        "delta_summary": sim_result["delta_summary"],
    }

    try:
        insert_prediction(record)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {str(e)}")

    sms_alert = _send_sms_alert(sim_result["simulated_risk"], source="Simulation")

    return {
        "real_risk": sim_result["real_risk"],
        "simulated_risk": sim_result["simulated_risk"],
        "simulated_probability": sim_result["simulated_probability"],
        "delta_summary": sim_result["delta_summary"],
        "similarity_insight": similarity_insight,
        "simulated_input": sim_result["simulated_input"],
        "sms_alert": sms_alert,
    }


@app.get("/history", summary="Return all stored predictions from MongoDB")
def history():
    """Returns every prediction and simulation record stored in MongoDB."""
    try:
        records = fetch_all_predictions()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {str(e)}")

    return {"total": len(records), "records": records}


@app.get("/high-risk", summary="Return only High-risk records from MongoDB")
def high_risk():
    """Returns all records where predicted_risk is 'High'."""
    try:
        records = fetch_high_risk_predictions()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {str(e)}")

    return {"total_high_risk": len(records), "records": records}


@app.get("/feature-columns", summary="Return model feature columns for frontend forms")
def feature_columns():
    """Returns feature names expected by the trained model."""
    if not MODEL_BUNDLE:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    return {
        "count": len(MODEL_BUNDLE["feature_cols"]),
        "feature_cols": MODEL_BUNDLE["feature_cols"],
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
