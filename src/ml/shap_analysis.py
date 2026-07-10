# src/ml/shap_analysis.py
"""
SHAP Explainability Analysis
=============================
Answers: "Why did the model flag this employee as high-risk?"

Uses TreeExplainer (fast, exact for tree-based models) to compute
SHAP values for the test set, then generates:
  1. Bar plot     — mean |SHAP| per feature (global importance)
  2. Beeswarm     — SHAP value distribution (how each feature pushes risk)
  3. Waterfall    — single highest-risk employee explained
  4. Dependence   — tenure_months vs SHAP value (partial effect)

Output: docs/plots/ml_shap_*.png
        data/processed/shap_feature_importance.csv

Run:
    python -m src.ml.shap_analysis
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
import shap

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PLOT_DIR   = os.path.join(ROOT, "docs", "plots")
PROC_DIR   = os.path.join(ROOT, "data", "processed")
MODELS_DIR = os.path.join(ROOT, "models")
TRAIN_CUTOFF = 2023

DARK_BG = "#0f1117"
AXES_BG = "#1a1d27"


def _load(feat: pd.DataFrame = None):
    model_path = os.path.join(MODELS_DIR, "attrition_model.pkl")
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    model, feature_cols = bundle["model"], bundle["feature_cols"]

    if feat is None:
        feat = pd.read_csv(os.path.join(PROC_DIR, "features.csv"))

    test   = feat[feat["joining_year"] > TRAIN_CUTOFF]
    X_test = test[feature_cols]
    y_test = test["attrition"]
    return model, X_test, y_test, feature_cols


def _save(fig, name):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


# ─────────────────────────────────────────────────────────────────────────────
def compute_shap(model, X_test: pd.DataFrame):
    """
    Use TreeExplainer — exact, fast for HistGradientBoosting.
    Returns shap_values (Explanation object) for the positive class.
    """
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    # For binary classifiers TreeExplainer returns shape (n, features, 2)
    # We want the positive class (attrition = 1)
    if shap_values.values.ndim == 3:
        import copy
        sv_pos = copy.copy(shap_values)
        sv_pos.values    = shap_values.values[:, :, 1]
        sv_pos.base_values = shap_values.base_values[:, 1]
        return sv_pos
    return shap_values


# ─────────────────────────────────────────────────────────────────────────────
def plot_bar(shap_values, feature_cols, top_n=20) -> str:
    """Global feature importance — mean |SHAP| values."""
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    imp_df   = pd.DataFrame({"feature": feature_cols, "mean_abs_shap": mean_abs})
    imp_df   = imp_df.sort_values("mean_abs_shap", ascending=True).tail(top_n)

    plt.rcParams.update({"figure.facecolor": DARK_BG, "text.color": "#e0e0e0",
                          "axes.facecolor": AXES_BG,   "axes.labelcolor": "#e0e0e0",
                          "xtick.color": "#a0a0a0",    "ytick.color": "#e0e0e0",
                          "grid.color": "#2a2d3a",     "grid.alpha": 0.4})

    fig, ax = plt.subplots(figsize=(10, 8), facecolor=DARK_BG)
    ax.set_facecolor(AXES_BG)

    colours = plt.cm.RdYlGn_r(
        np.linspace(0.1, 0.9, len(imp_df))
    )
    bars = ax.barh(imp_df["feature"], imp_df["mean_abs_shap"],
                   color=colours, alpha=0.85, edgecolor="#1a1d27")

    for bar, val in zip(bars, imp_df["mean_abs_shap"]):
        ax.text(val + 0.0005, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", ha="left",
                color="#e0e0e0", fontsize=7.5)

    ax.set_xlabel("Mean |SHAP Value|  (average impact on model output)", fontsize=11)
    ax.set_title(f"Top {top_n} Features by Global Importance  (SHAP)",
                 fontsize=14, fontweight="bold", color="#fff", pad=10)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "ml_shap_01_bar.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_beeswarm(shap_values, top_n=15) -> str:
    """Beeswarm: how each feature's values push predictions up or down."""
    plt.rcParams.update({"figure.facecolor": DARK_BG, "text.color": "#e0e0e0",
                          "axes.facecolor": AXES_BG})
    fig, ax = plt.subplots(figsize=(11, 8), facecolor=DARK_BG)
    shap.plots.beeswarm(shap_values, max_display=top_n, show=False,
                         plot_size=None)
    fig = plt.gcf()
    fig.patch.set_facecolor(DARK_BG)
    for a in fig.axes:
        a.set_facecolor(AXES_BG)
    fig.suptitle("SHAP Beeswarm Plot — Feature Impact Distribution",
                 fontsize=13, fontweight="bold", color="#fff", y=1.01)
    fig.tight_layout()
    return _save(fig, "ml_shap_02_beeswarm.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_waterfall(shap_values, y_prob: np.ndarray, idx: int = None) -> str:
    """Waterfall plot for a single high-risk employee."""
    if idx is None:
        idx = int(np.argmax(y_prob))    # highest predicted risk

    plt.rcParams.update({"figure.facecolor": DARK_BG, "text.color": "#e0e0e0",
                          "axes.facecolor": AXES_BG})
    fig, ax = plt.subplots(figsize=(11, 8), facecolor=DARK_BG)
    shap.plots.waterfall(shap_values[idx], max_display=15, show=False)
    fig = plt.gcf()
    fig.patch.set_facecolor(DARK_BG)
    for a in fig.axes:
        a.set_facecolor(AXES_BG)
    risk_pct = y_prob[idx] * 100
    fig.suptitle(
        f"SHAP Waterfall — Highest-Risk Employee  (Risk Score: {risk_pct:.1f}%)",
        fontsize=13, fontweight="bold", color="#fff", y=1.01
    )
    fig.tight_layout()
    return _save(fig, "ml_shap_03_waterfall.png")


# ─────────────────────────────────────────────────────────────────────────────
def plot_dependence(shap_values, X_test: pd.DataFrame, feature: str = "tenure_months") -> str:
    """Dependence plot: SHAP value vs feature value for one feature."""
    plt.rcParams.update({"figure.facecolor": DARK_BG, "text.color": "#e0e0e0",
                          "axes.facecolor": AXES_BG,   "axes.labelcolor": "#e0e0e0",
                          "xtick.color": "#a0a0a0",    "ytick.color": "#a0a0a0",
                          "grid.color": "#2a2d3a",     "grid.alpha": 0.4})

    if feature not in X_test.columns:
        feature = X_test.columns[0]

    feat_idx  = list(X_test.columns).index(feature)
    feat_vals = X_test[feature].values
    shap_vals = shap_values.values[:, feat_idx]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=DARK_BG)
    ax.set_facecolor(AXES_BG)

    sc = ax.scatter(feat_vals, shap_vals, c=feat_vals, cmap="plasma",
                    alpha=0.4, s=8, linewidths=0)
    plt.colorbar(sc, ax=ax, label=feature)
    ax.axhline(0, color="#555566", lw=1, ls="--")

    ax.set_xlabel(feature, fontsize=11)
    ax.set_ylabel(f"SHAP value for {feature}", fontsize=11)
    ax.set_title(f"SHAP Dependence Plot — {feature}",
                 fontsize=14, fontweight="bold", color="#fff", pad=10)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return _save(fig, f"ml_shap_04_dependence_{feature}.png")


# ─────────────────────────────────────────────────────────────────────────────
def save_feature_importance(shap_values, feature_cols: list) -> str:
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    df = pd.DataFrame({
        "feature":        feature_cols,
        "mean_abs_shap":  mean_abs.round(6),
        "rank":           pd.Series(mean_abs).rank(ascending=False).astype(int).values,
    }).sort_values("rank")
    path = os.path.join(PROC_DIR, "shap_feature_importance.csv")
    df.to_csv(path, index=False)
    return path


# ─────────────────────────────────────────────────────────────────────────────
def run_shap_analysis(feat: pd.DataFrame = None) -> list[str]:
    print("  Computing SHAP values (TreeExplainer)…")
    model, X_test, y_test, feature_cols = _load(feat)
    y_prob       = model.predict_proba(X_test)[:, 1]
    shap_values  = compute_shap(model, X_test)

    # Save CSV
    csv_path = save_feature_importance(shap_values, feature_cols)
    print(f"  ✓  shap_feature_importance.csv")

    paths = []
    for fn, args, label in [
        (plot_bar,        (shap_values, feature_cols),    "ml_shap_01_bar.png"),
        (plot_beeswarm,   (shap_values,),                  "ml_shap_02_beeswarm.png"),
        (plot_waterfall,  (shap_values, y_prob),           "ml_shap_03_waterfall.png"),
        (plot_dependence, (shap_values, X_test),           "ml_shap_04_dependence_tenure_months.png"),
    ]:
        p = fn(*args)
        print(f"  ✓  {os.path.basename(p)}")
        paths.append(p)

    return paths


if __name__ == "__main__":
    run_shap_analysis()
