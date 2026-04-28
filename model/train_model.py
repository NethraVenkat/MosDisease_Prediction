# train_model.py
# Trains a RandomForestClassifier on the dengue dataset and saves it as model.pkl
# Run this script once before starting the API: python -m model.train_model

import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# Add project root to path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MosDisease_Prediction.backend.config import DATASET_PATH, MODEL_PATH


def detect_numeric_columns(df: pd.DataFrame) -> list:
    """Return all numeric columns from the DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the most likely 'cases' column by checking common column names.
    Falls back to the last numeric column.
    """
    candidates = ["total_cases", "cases", "num_cases", "dengue_cases", "case_count"]
    for col in candidates:
        if col in df.columns:
            return col
    numeric_cols = detect_numeric_columns(df)
    if numeric_cols:
        return numeric_cols[-1]
    raise ValueError("No suitable target column found in the dataset.")


def create_risk_label(series: pd.Series) -> pd.Series:
    """
    Create a risk label column based on percentile thresholds:
      Low    → below 33rd percentile
      Medium → 33rd to 66th percentile
      High   → above 66th percentile
    """
    low_thresh = series.quantile(0.33)
    high_thresh = series.quantile(0.66)

    def classify(val):
        if val <= low_thresh:
            return "Low"
        elif val <= high_thresh:
            return "Medium"
        else:
            return "High"

    return series.apply(classify)


def train():
    print("=" * 60)
    print("  Disease Outbreak Hotspot Predictor — Model Training")
    print("=" * 60)

    # Load dataset
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found at '{DATASET_PATH}'.\n"
            "Please place dengue.csv inside the data/ folder."
        )

    df = pd.read_csv(DATASET_PATH)
    print(f"\n[INFO] Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"[INFO] Columns detected: {list(df.columns)}")

    # Drop columns that are entirely non-numeric (e.g., city, year strings)
    df = df.dropna(axis=1, how="all")

    # Detect the cases/target column
    target_col = detect_target_column(df)
    print(f"[INFO] Using '{target_col}' as the target (cases) column.")

    # Create risk label
    df["risk"] = create_risk_label(df[target_col])

    # Select numeric feature columns (exclude the target column itself)
    numeric_cols = detect_numeric_columns(df)
    feature_cols = [c for c in numeric_cols if c != target_col]

    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found after removing the target.")

    print(f"[INFO] Feature columns: {feature_cols}")
    print(f"[INFO] Risk label distribution:\n{df['risk'].value_counts()}\n")

    # Prepare features and labels
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df["risk"]

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Train RandomForest
    clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[INFO] Model Accuracy: {acc * 100:.2f}%")
    print("\n[INFO] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Bundle model artifacts
    model_bundle = {
        "model": clf,
        "label_encoder": le,
        "feature_cols": feature_cols,
        "target_col": target_col,
        "low_thresh": df[target_col].quantile(0.33),
        "high_thresh": df[target_col].quantile(0.66),
    }

    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_bundle, f)

    print(f"\n[SUCCESS] Model saved to '{MODEL_PATH}'")
    print("=" * 60)

    return model_bundle


if __name__ == "__main__":
    train()
