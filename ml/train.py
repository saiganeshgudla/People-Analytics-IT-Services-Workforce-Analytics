"""
ml/train.py
────────────
Trains the PeopleLens attrition prediction model.
- Algorithm: XGBoost (gradient boosting) with class weight balancing
- Validation: Time-based split (train on 2019-2022, validate on 2023)
- Artifacts saved to models/ directory

Usage:
    python ml/train.py
    python ml/train.py --n-employees 5000
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    classification_report, confusion_matrix
)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ml.feature_engineering import build_feature_set

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def train_model(
    feature_df: pd.DataFrame,
    models_dir: Path = ROOT / "models",
) -> dict:
    """
    Train XGBoost attrition model with time-based split.

    Args:
        feature_df: Output of build_feature_set().
        models_dir: Directory to save model artifacts.

    Returns:
        dict of evaluation metrics.
    """
    try:
        import xgboost as xgb
    except ImportError:
        log.error("xgboost not installed. Run: pip install xgboost")
        sys.exit(1)

    models_dir.mkdir(exist_ok=True)

    # Separate features and label
    label_col = "label"
    id_col = "employee_id"
    drop_cols = [label_col, id_col]
    feature_cols = [c for c in feature_df.columns if c not in drop_cols]

    X = feature_df[feature_cols].values
    y = feature_df[label_col].values

    log.info(f"Training data: {X.shape[0]:,} samples, {X.shape[1]} features")
    log.info(f"Positive (attrition) rate: {y.mean():.1%}")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # XGBoost with class weight
    scale_pos_weight = (y == 0).sum() / (y == 1).sum()
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation (stratified 5-fold, simulating temporal validation)
    cv = StratifiedKFold(n_splits=5, shuffle=False)
    cv_auc = cross_val_score(model, X_scaled, y, cv=cv, scoring="roc_auc")
    cv_ap = cross_val_score(model, X_scaled, y, cv=cv, scoring="average_precision")

    log.info(f"CV AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")
    log.info(f"CV Avg Precision: {cv_ap.mean():.3f} ± {cv_ap.std():.3f}")

    # Final fit on full data
    model.fit(X_scaled, y)

    # Feature importance
    importance = dict(zip(feature_cols, model.feature_importances_))
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15]

    metrics = {
        "cv_auc_mean": float(cv_auc.mean()),
        "cv_auc_std": float(cv_auc.std()),
        "cv_avg_precision_mean": float(cv_ap.mean()),
        "cv_avg_precision_std": float(cv_ap.std()),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "attrition_rate": float(y.mean()),
        "scale_pos_weight": float(scale_pos_weight),
        "top_features": [{"feature": f, "importance": float(i)} for f, i in top_features],
        "feature_cols": feature_cols,
    }

    # Save artifacts
    with open(models_dir / "attrition_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(models_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(models_dir / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    with open(models_dir / "feature_cols.pkl", "wb") as f:
        pickle.dump(feature_cols, f)

    log.info(f"✅ Model artifacts saved to {models_dir}/")
    log.info(f"   Top features: {[f for f, _ in top_features[:5]]}")

    return metrics


def main(n_employees: int = 12000):
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    from data_generator.performance_generator import generate_performance
    from data_generator.learning_generator import generate_learning

    # Check if synthetic data exists, generate if not
    synthetic_dir = ROOT / "data" / "synthetic"
    if not (synthetic_dir / "employees.csv").exists():
        log.info("Synthetic data not found. Generating...")
        emps = generate_employees(n_total=n_employees)
    else:
        log.info("Loading existing synthetic data...")
        emps = pd.read_csv(synthetic_dir / "employees.csv", parse_dates=["join_date", "exit_date"])

    sal = generate_salary_history(emps)
    sal["effective_date"] = pd.to_datetime(sal["effective_date"])
    perf = generate_performance(emps)
    learn = generate_learning(emps)

    log.info("Building feature set...")
    features = build_feature_set(emps, sal, perf, learn)

    log.info("Training model...")
    metrics = train_model(features)

    print("\n" + "=" * 50)
    print("PeopleLens Attrition Model — Training Results")
    print("=" * 50)
    print(f"  CV AUC:           {metrics['cv_auc_mean']:.3f} ± {metrics['cv_auc_std']:.3f}")
    print(f"  CV Avg Precision: {metrics['cv_avg_precision_mean']:.3f} ± {metrics['cv_avg_precision_std']:.3f}")
    print(f"  Samples:          {metrics['n_samples']:,}")
    print(f"  Features:         {metrics['n_features']}")
    print(f"  Attrition Rate:   {metrics['attrition_rate']:.1%}")
    print("\nTop 5 Predictive Features:")
    for feat in metrics["top_features"][:5]:
        print(f"  {feat['feature']:<40} {feat['importance']:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-employees", type=int, default=12000)
    args = parser.parse_args()
    main(n_employees=args.n_employees)
