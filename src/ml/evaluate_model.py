# src/ml/evaluate_model.py
"""
Model Evaluation & Diagnostic Plots
=====================================
Generates the four canonical classification evaluation charts:
  1. ROC Curve          — AUC measure of discrimination power
  2. Precision-Recall   — critical for imbalanced datasets (15% positive)
  3. Confusion Matrix   — heatmap of TP/FP/FN/TN
  4. Risk Score Distribution — histogram of predicted probabilities by class

Output: docs/plots/ml_*.png

Run:
    python -m src.ml.evaluate_model
"""

import os
import sys
import pickle
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sklearn.metrics import (
    roc_curve, auc,
    precision_recall_curve, average_precision_score,
    confusion_matrix,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PLOT_DIR   = os.path.join(ROOT, "docs", "plots")
PROC_DIR   = os.path.join(ROOT, "data", "processed")
MODELS_DIR = os.path.join(ROOT, "models")

DARK = {
    "figure.facecolor": "#0f1117", "axes.facecolor": "#1a1d27",
    "axes.edgecolor": "#3a3f52",   "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#a0a0a0",      "ytick.color": "#a0a0a0",
    "grid.color": "#2a2d3a",       "grid.linestyle": "--",
    "grid.alpha": 0.4,             "text.color": "#e0e0e0",
    "legend.facecolor": "#1e2130", "legend.edgecolor": "#3a3f52",
    "legend.labelcolor": "#e0e0e0",
}

TRAIN_CUTOFF = 2023


def _load(feat: pd.DataFrame = None):
    """Load model bundle and prepare test split."""
    model_path = os.path.join(MODELS_DIR, "attrition_model.pkl")
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    model, feature_cols = bundle["model"], bundle["feature_cols"]

    if feat is None:
        feat = pd.read_csv(os.path.join(PROC_DIR, "features.csv"))

    test = feat[feat["joining_year"] > TRAIN_CUTOFF]
    X_test = test[feature_cols]
    y_test = test["attrition"]
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    return model, X_test, y_test, y_pred, y_prob


def _save(fig, name):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
def plot_roc(y_test, y_prob) -> str:
    plt.rcParams.update(DARK)
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=DARK["figure.facecolor"])
    ax.set_facecolor(DARK["axes.facecolor"])

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc     = auc(fpr, tpr)

    ax.plot(fpr, tpr, color="#4C72B0", lw=2.5,
            label=f"ROC Curve  (AUC = {roc_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="#555566", lw=1.2,
            linestyle="--", label="Random Classifier (AUC = 0.50)")
    ax.fill_between(fpr, tpr, alpha=0.08, color="#4C72B0")

    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
    ax.set_title("ROC Curve — Attrition Prediction Model",
                 fontsize=14, fontweight="bold", color="#fff", pad=10)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, "ml_01_roc_curve.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_precision_recall(y_test, y_prob) -> str:
    plt.rcParams.update(DARK)
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=DARK["figure.facecolor"])
    ax.set_facecolor(DARK["axes.facecolor"])

    prec, rec, _ = precision_recall_curve(y_test, y_prob)
    ap           = average_precision_score(y_test, y_prob)
    baseline     = y_test.mean()

    ax.plot(rec, prec, color="#DD8452", lw=2.5,
            label=f"PR Curve  (AP = {ap:.4f})")
    ax.axhline(baseline, color="#555566", lw=1.2, linestyle="--",
               label=f"No-skill baseline ({baseline:.2f})")
    ax.fill_between(rec, prec, alpha=0.08, color="#DD8452")

    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_title("Precision-Recall Curve  (Imbalanced Class = 15% Attrition)",
                 fontsize=13, fontweight="bold", color="#fff", pad=10)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, "ml_02_precision_recall.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_confusion_matrix(y_test, y_pred) -> str:
    plt.rcParams.update(DARK)
    fig, ax = plt.subplots(figsize=(7, 6), facecolor=DARK["figure.facecolor"])
    ax.set_facecolor(DARK["axes.facecolor"])

    cm     = confusion_matrix(y_test, y_pred)
    labels = np.array([["TN\n(Correct: Active)", "FP\n(False Alarm)"],
                        ["FN\n(Missed Exit)", "TP\n(Caught Exit)"]])

    im = ax.imshow(cm, interpolation="nearest", cmap="Blues", vmin=0)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    for i in range(2):
        for j in range(2):
            colour = "white" if cm[i, j] > cm.max() / 2 else "#e0e0e0"
            ax.text(j, i, f"{cm[i, j]:,}\n{labels[i, j]}",
                    ha="center", va="center", fontsize=10.5,
                    color=colour, fontweight="bold")

    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted: Active (0)", "Predicted: Exit (1)"],
                        fontsize=10, color="#e0e0e0")
    ax.set_yticklabels(["Actual: Active (0)", "Actual: Exit (1)"],
                        fontsize=10, color="#e0e0e0")
    ax.set_title("Confusion Matrix — Test Set",
                 fontsize=14, fontweight="bold", color="#fff", pad=12)
    fig.tight_layout()
    return _save(fig, "ml_03_confusion_matrix.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_risk_distribution(y_test, y_prob) -> str:
    plt.rcParams.update(DARK)
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=DARK["figure.facecolor"])
    ax.set_facecolor(DARK["axes.facecolor"])

    active_probs = y_prob[y_test == 0]
    exited_probs = y_prob[y_test == 1]

    bins = np.linspace(0, 1, 41)
    ax.hist(active_probs, bins=bins, alpha=0.65, color="#2ecc71",
            label=f"Active employees  (n={len(active_probs):,})", edgecolor="none")
    ax.hist(exited_probs, bins=bins, alpha=0.75, color="#e74c3c",
            label=f"Exited employees  (n={len(exited_probs):,})", edgecolor="none")

    ax.axvline(0.5, color="#f1c40f", lw=1.5, linestyle="--",
               label="Decision threshold (0.50)")
    ax.set_xlabel("Predicted Attrition Probability (Risk Score)", fontsize=11)
    ax.set_ylabel("Employee Count", fontsize=11)
    ax.set_title("Risk Score Distribution by True Label",
                 fontsize=14, fontweight="bold", color="#fff", pad=10)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, "ml_04_risk_distribution.png")


# ─────────────────────────────────────────────────────────────────────────────
def run_evaluation(feat: pd.DataFrame = None) -> list[str]:
    model, X_test, y_test, y_pred, y_prob = _load(feat)

    print("  Generating evaluation plots…")
    paths = []
    for fn, args in [
        (plot_roc,               (y_test, y_prob)),
        (plot_precision_recall,  (y_test, y_prob)),
        (plot_confusion_matrix,  (y_test, y_pred)),
        (plot_risk_distribution, (y_test, y_prob)),
    ]:
        p = fn(*args)
        print(f"  ✓  {os.path.basename(p)}")
        paths.append(p)
    return paths


if __name__ == "__main__":
    run_evaluation()
