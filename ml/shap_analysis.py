"""
ml/shap_analysis.py
──────────────────────
SHAP (SHapley Additive exPlanations) analysis for the attrition model.
Generates global feature importance and per-employee explanations.

Output:
- models/shap_values.pkl (for dashboard consumption)
- Plots: waterfall chart, beeswarm plot (saved as PNG in docs/images/)
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


def compute_shap_values(
    feature_df: pd.DataFrame,
    models_dir: Path = ROOT / "models",
    n_sample: int = 500,
) -> dict:
    """
    Compute SHAP values for the trained attrition model.

    Args:
        feature_df: Feature set DataFrame.
        models_dir: Directory with model artifacts.
        n_sample: Number of samples for SHAP (subsample for speed).

    Returns:
        dict with shap_values array and expected_value.
    """
    try:
        import shap
    except ImportError:
        log.error("shap not installed. Run: pip install shap")
        return {}

    model_path = models_dir / "attrition_model.pkl"
    scaler_path = models_dir / "scaler.pkl"
    feature_cols_path = models_dir / "feature_cols.pkl"

    if not model_path.exists():
        log.error("Model not found. Run ml/train.py first.")
        return {}

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(feature_cols_path, "rb") as f:
        feature_cols = pickle.load(f)

    # Align columns
    for col in feature_cols:
        if col not in feature_df.columns:
            feature_df[col] = 0
    X = feature_df[feature_cols].values

    # Sample for SHAP computation
    idx = np.random.choice(len(X), size=min(n_sample, len(X)), replace=False)
    X_sample = scaler.transform(X[idx])

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # Global feature importance
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False)

    result = {
        "shap_values": shap_values,
        "expected_value": float(explainer.expected_value),
        "feature_names": feature_cols,
        "X_sample": X_sample,
        "importance_df": importance_df,
    }

    # Save for dashboard
    with open(models_dir / "shap_values.pkl", "wb") as f:
        pickle.dump(result, f)

    log.info(f"SHAP analysis complete. Top features: {importance_df['feature'].head(5).tolist()}")
    return result


if __name__ == "__main__":
    from ml.feature_engineering import build_feature_set
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    from data_generator.performance_generator import generate_performance
    from data_generator.learning_generator import generate_learning

    emps = generate_employees(n_total=2000, seed=42)
    sal = generate_salary_history(emps)
    sal["effective_date"] = pd.to_datetime(sal["effective_date"])
    perf = generate_performance(emps)
    learn = generate_learning(emps)

    features = build_feature_set(emps, sal, perf, learn)
    result = compute_shap_values(features)
    if result:
        print("Top 10 features by SHAP importance:")
        print(result["importance_df"].head(10).to_string(index=False))
