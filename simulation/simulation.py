# simulate.py
# Digital Twin simulation module.
# Takes a real input, applies percentage changes to selected parameters,
# predicts the new risk, and returns a comparison.

import copy
import numpy as np


def apply_delta(value: float, delta_percent: float) -> float:
    """Increase or decrease a value by delta_percent (e.g., +20 means +20%)."""
    return value * (1 + delta_percent / 100.0)


def run_simulation(
    model_bundle: dict,
    original_input: dict,
    rainfall_delta: float = 0.0,
    humidity_delta: float = 0.0,
    temperature_delta: float = 0.0,
    original_risk: str = "Unknown",
) -> dict:
    """
    Simulate how changes in environmental conditions affect disease outbreak risk.

    Parameters:
        model_bundle     : dict with keys 'model', 'label_encoder', 'feature_cols'
        original_input   : dict mapping feature names to their real values
        rainfall_delta   : percentage change to apply to the rainfall feature
        humidity_delta   : percentage change to apply to the humidity feature
        temperature_delta: percentage change to apply to the temperature feature
        original_risk    : the predicted risk from the original (real) input

    Returns:
        {
            "original_input": {...},
            "simulated_input": {...},
            "real_risk": "...",
            "simulated_risk": "...",
            "simulated_probability": float,
            "delta_summary": "...",
        }
    """
    clf = model_bundle["model"]
    le = model_bundle["label_encoder"]
    feature_cols = model_bundle["feature_cols"]

    # Build the simulated input by copying the original
    simulated_input = copy.deepcopy(original_input)

    # Map common keywords to feature column names found in the dataset
    keyword_map = {
        "rainfall": rainfall_delta,
        "rain": rainfall_delta,
        "precipitation": rainfall_delta,
        "humidity": humidity_delta,
        "relative_humidity": humidity_delta,
        "temperature": temperature_delta,
        "temp": temperature_delta,
        "avg_temp": temperature_delta,
        "station_avg_temp": temperature_delta,
    }

    applied_changes = []
    for col in feature_cols:
        col_lower = col.lower()
        for keyword, delta in keyword_map.items():
            if keyword in col_lower and delta != 0.0:
                if col in simulated_input:
                    old_val = simulated_input[col]
                    simulated_input[col] = apply_delta(old_val, delta)
                    applied_changes.append(
                        f"{col}: {old_val:.2f} → {simulated_input[col]:.2f} ({delta:+.1f}%)"
                    )
                break

    # Build feature vector for the simulated input
    sim_vector = np.array([[simulated_input.get(c, 0.0) for c in feature_cols]])

    sim_pred_encoded = clf.predict(sim_vector)[0]
    sim_proba = clf.predict_proba(sim_vector)[0]
    sim_risk = le.inverse_transform([sim_pred_encoded])[0]
    sim_probability = round(float(max(sim_proba)), 4)

    change_summary = (
        "; ".join(applied_changes)
        if applied_changes
        else "No recognised environmental parameters were modified."
    )

    comparison = "remained the same"
    if sim_risk != original_risk:
        comparison = f"changed from {original_risk} → {sim_risk}"

    delta_summary = (
        f"Simulation applied: [{change_summary}]. "
        f"Outbreak risk {comparison}. "
        f"Model confidence in simulated risk: {sim_probability * 100:.1f}%."
    )

    return {
        "original_input": original_input,
        "simulated_input": simulated_input,
        "real_risk": original_risk,
        "simulated_risk": sim_risk,
        "simulated_probability": sim_probability,
        "delta_summary": delta_summary,
    }
