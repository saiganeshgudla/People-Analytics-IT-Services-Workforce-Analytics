"""
ml/predict.py
──────────────
Batch inference: loads trained model, generates attrition risk scores
for all currently active employees.

Output: data/analytics/attrition_scores.csv
  - employee_id, risk_score (0-1), risk_tier (Low/Medium/High)
"""

from __future__ import annotations

import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

RISK_THRESHOLDS = {"Low": 0.30, "Medium": 0.60, "High": 1.0}


def predict_attrition_risk(
    feature_df: pd.DataFrame,
    models_dir: Path = ROOT / "models",
) -> pd.DataFrame:
    """
    Run batch inference on feature set.

    Args:
        feature_df: Output of build_feature_set().
        models_dir: Directory containing saved model artifacts.

    Returns:
        DataFrame with employee_id, risk_score, risk_tier.
    """
    model_path = models_dir / "attrition_model.pkl"
    scaler_path = models_dir / "scaler.pkl"
    feature_cols_path = models_dir / "feature_cols.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run ml/train.py first.")

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(feature_cols_path, "rb") as f:
        feature_cols = pickle.load(f)

    # Align feature columns (add missing as 0, drop extras)
    for col in feature_cols:
        if col not in feature_df.columns:
            feature_df[col] = 0
    X = feature_df[feature_cols].values

    X_scaled = scaler.transform(X)
    risk_scores = model.predict_proba(X_scaled)[:, 1]

    result = pd.DataFrame({
        "employee_id": feature_df["employee_id"] if "employee_id" in feature_df.columns else range(len(risk_scores)),
        "risk_score": risk_scores.round(4),
    })

    result["risk_tier"] = pd.cut(
        result["risk_score"],
        bins=[0, 0.30, 0.60, 1.0],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )

    log.info(f"Risk predictions: {len(result):,} employees")
    log.info(f"  High risk: {(result['risk_tier'] == 'High').sum():,} ({(result['risk_tier'] == 'High').mean():.1%})")
    log.info(f"  Medium risk: {(result['risk_tier'] == 'Medium').sum():,}")
    log.info(f"  Low risk: {(result['risk_tier'] == 'Low').sum():,}")

    return result


if __name__ == "__main__":
    from ml.feature_engineering import build_feature_set
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    from data_generator.performance_generator import generate_performance
    from data_generator.learning_generator import generate_learning

    emps = generate_employees(n_total=3000, seed=42)
    sal = generate_salary_history(emps)
    sal["effective_date"] = pd.to_datetime(sal["effective_date"])
    perf = generate_performance(emps)
    learn = generate_learning(emps)

    features = build_feature_set(emps, sal, perf, learn)
    scores = predict_attrition_risk(features)
    output_path = ROOT / "data" / "analytics" / "attrition_scores.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(output_path, index=False)
    print(scores.head(10).to_string())
