"""
ml/evaluate.py
───────────────
Model evaluation: AUC, precision-recall, calibration, confusion matrix.
Outputs evaluation report to models/model_metrics.json.
"""

from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    precision_recall_curve, roc_curve,
    classification_report, brier_score_loss,
)
from sklearn.calibration import calibration_curve

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
log = logging.getLogger(__name__)


def evaluate_model(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.40,
) -> dict:
    """
    Compute comprehensive evaluation metrics.

    Args:
        y_true: True binary labels.
        y_pred_proba: Predicted probabilities for the positive class.
        threshold: Decision threshold for binary classification.

    Returns:
        dict with all evaluation metrics.
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    auc = roc_auc_score(y_true, y_pred_proba)
    avg_precision = average_precision_score(y_true, y_pred_proba)
    brier = brier_score_loss(y_true, y_pred_proba)
    report = classification_report(y_true, y_pred, output_dict=True)

    # ROC curve points (sample 100 for storage efficiency)
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    idx = np.linspace(0, len(fpr) - 1, min(100, len(fpr)), dtype=int)

    # Calibration
    fraction_pos, mean_pred = calibration_curve(y_true, y_pred_proba, n_bins=10)

    metrics = {
        "roc_auc": float(auc),
        "average_precision": float(avg_precision),
        "brier_score": float(brier),
        "threshold": threshold,
        "precision_at_threshold": float(report.get("1", {}).get("precision", 0)),
        "recall_at_threshold": float(report.get("1", {}).get("recall", 0)),
        "f1_at_threshold": float(report.get("1", {}).get("f1-score", 0)),
        "roc_curve": {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()},
        "calibration": {
            "fraction_pos": fraction_pos.tolist(),
            "mean_pred": mean_pred.tolist(),
        },
    }

    log.info(f"AUC: {auc:.3f} | Avg Precision: {avg_precision:.3f} | Brier: {brier:.4f}")
    return metrics


if __name__ == "__main__":
    print("Run ml/train.py first to generate model artifacts, then evaluation is embedded there.")
