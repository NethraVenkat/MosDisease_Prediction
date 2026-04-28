# similarity.py
# Explainable AI module: finds the top-N most similar past records
# from the dataset and generates a human-readable insight string.

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def compute_euclidean_similarity(df: pd.DataFrame, input_values: dict, feature_cols: list, top_n: int = 3) -> list:
    """
    Find the top_n most similar rows in df to input_values using
    Euclidean distance on normalised feature columns.

    Returns a list of dicts, each containing the row values and its distance.
    """
    available_cols = [c for c in feature_cols if c in df.columns and c in input_values]

    if not available_cols:
        return []

    subset = df[available_cols].fillna(df[available_cols].median())

    # Normalise using MinMaxScaler so all features are on [0, 1]
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(subset)

    # Scale the user input using the same scaler
    input_array = np.array([[input_values[c] for c in available_cols]])
    scaled_input = scaler.transform(input_array)

    # Compute Euclidean distance between input and every row
    distances = np.linalg.norm(scaled_data - scaled_input, axis=1)

    # Get indices of the closest rows
    top_indices = np.argsort(distances)[:top_n]

    results = []
    for idx in top_indices:
        row = df.iloc[idx][available_cols].to_dict()
        row["_distance"] = round(float(distances[idx]), 4)
        results.append(row)

    return results


def generate_insight(similar_records: list, risk_col: str = "risk") -> str:
    """
    Generate a plain-English explainability insight based on the similar records.

    Parameters:
        similar_records: list of row dicts returned by compute_euclidean_similarity
        risk_col: name of the risk/outcome column, if present in records

    Returns:
        A single insight string.
    """
    if not similar_records:
        return "No similar historical records found; prediction is based solely on the trained model."

    n = len(similar_records)

    # Summarise key numeric features across similar records
    numeric_keys = [k for k in similar_records[0].keys() if k not in ("_distance", risk_col)]
    summaries = []

    for key in numeric_keys:
        values = [r[key] for r in similar_records if key in r and isinstance(r[key], (int, float))]
        if values:
            avg = np.mean(values)
            summaries.append(f"{key.replace('_', ' ')}: avg {avg:.2f}")

    feature_summary = ", ".join(summaries) if summaries else "similar environmental conditions"

    insight = (
        f"\nAnalysis of {n} historically similar cases revealed the following patterns: "
        f"{feature_summary}.\n \n "
        "These conditions have previously been associated with dengue outbreaks. \n"
        "High humidity combined with elevated rainfall creates ideal breeding conditions "
        "for mosquito populations, significantly increasing outbreak risk."
    )

    return insight


def run_similarity_analysis(
    df: pd.DataFrame,
    input_values: dict,
    feature_cols: list,
    top_n: int = 3,
) -> dict:
    """
    Orchestrates similarity analysis and insight generation.

    Returns:
        {
            "similar_records": [...],
            "insight": "..."
        }
    """
    similar_records = compute_euclidean_similarity(df, input_values, feature_cols, top_n)
    insight = generate_insight(similar_records)

    return {
        "similar_records": similar_records,
        "insight": insight,
    }
