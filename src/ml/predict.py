# src/ml/predict.py
"""
Attrition Risk Scoring & Predictions
======================================
Applies the trained model to ALL employees (including active ones)
to generate a risk score 0–100 for intervention planning.

Privacy: Outputs are aggregated by department/manager (k ≥ 10)
         to comply with k-anonymity requirements before dashboard use.

Outputs:
  data/processed/predictions.csv          — individual risk scores
  data/processed/dept_risk_summary.csv    — dept-level aggregated risk
  data/processed/manager_risk_summary.csv — manager-level (k ≥ 10 only)

Run:
    python -m src.ml.predict
"""

import os
import sys
import pickle
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PROC_DIR   = os.path.join(ROOT, "data", "processed")
MODELS_DIR = os.path.join(ROOT, "models")
RAW_DIR    = os.path.join(ROOT, "data", "synthetic")

GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
CYAN   = "\033[96m"; BOLD = "\033[1m"; RESET  = "\033[0m"; W = 64
def _c(t, c): return f"{c}{t}{RESET}"
def _h(t):    print(_c("="*W, CYAN)); print(_c(f"  {t}", BOLD+CYAN)); print(_c("="*W, CYAN))
def _s(t):    print(f"\n{_c(BOLD+t, BOLD)}"); print(_c("-"*W, CYAN))

K_ANONYMITY = 10   # minimum group size for aggregated outputs


def load_model():
    path = os.path.join(MODELS_DIR, "attrition_model.pkl")
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["feature_cols"]


# ─────────────────────────────────────────────────────────────────────────────
def score_all_employees(feat: pd.DataFrame, model, feature_cols: list) -> pd.DataFrame:
    """
    Add risk_score (0–100), risk_tier, and predicted_attrition to feat.
    """
    X    = feat[feature_cols]
    prob = model.predict_proba(X)[:, 1]
    pred = model.predict(X)

    feat = feat.copy()
    feat["risk_score"]         = (prob * 100).round(1)
    feat["predicted_attrition"]= pred
    feat["attrition_prob"]     = prob.round(4)

    feat["risk_tier"] = pd.cut(
        feat["risk_score"],
        bins   = [0, 20, 40, 60, 80, 100],
        labels = ["Very Low", "Low", "Medium", "High", "Critical"],
        right  = True
    )
    return feat


# ─────────────────────────────────────────────────────────────────────────────
def build_dept_summary(predictions: pd.DataFrame, raw_emp: pd.DataFrame) -> pd.DataFrame:
    """
    Department-level aggregated risk (Power BI card / bar chart source).
    Merges department back from the raw employee table.
    """
    # Re-attach department (was one-hot encoded in features)
    emp_meta = raw_emp[["employee_id", "department", "status"]]
    df = predictions.merge(emp_meta, on="employee_id", how="left")

    summary = df.groupby("department").agg(
        total_employees    = ("employee_id", "count"),
        avg_risk_score     = ("risk_score",  "mean"),
        high_risk_count    = ("risk_score",  lambda x: (x >= 60).sum()),
        critical_risk_count= ("risk_score",  lambda x: (x >= 80).sum()),
        actual_exits       = ("attrition",   "sum"),
        predicted_exits    = ("predicted_attrition", "sum"),
    ).reset_index()

    summary["avg_risk_score"]  = summary["avg_risk_score"].round(1)
    summary["high_risk_pct"]   = (
        summary["high_risk_count"] / summary["total_employees"] * 100
    ).round(1)
    return summary.sort_values("avg_risk_score", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
def build_manager_summary(predictions: pd.DataFrame, raw_emp: pd.DataFrame) -> pd.DataFrame:
    """
    Manager-level aggregated risk — k-anonymity enforced (k ≥ 10).
    Groups with < 10 employees are suppressed.
    """
    emp_meta = raw_emp[["employee_id", "manager_id", "status"]]
    df = predictions.merge(emp_meta, on="employee_id", how="left")

    summary = df.groupby("manager_id").agg(
        team_size          = ("employee_id", "count"),
        avg_risk_score     = ("risk_score",  "mean"),
        high_risk_count    = ("risk_score",  lambda x: (x >= 60).sum()),
        actual_exits       = ("attrition",   "sum"),
        predicted_exits    = ("predicted_attrition", "sum"),
    ).reset_index()

    # k-anonymity: suppress groups with < 10 employees
    before = len(summary)
    summary = summary[summary["team_size"] >= K_ANONYMITY].copy()
    suppressed = before - len(summary)

    summary["avg_risk_score"]  = summary["avg_risk_score"].round(1)
    summary["high_risk_pct"]   = (
        summary["high_risk_count"] / summary["team_size"] * 100
    ).round(1)

    if suppressed > 0:
        print(f"  ⚠  {suppressed} managers suppressed (team size < {K_ANONYMITY}, k-anonymity)")

    return summary.sort_values("avg_risk_score", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
def print_risk_report(predictions: pd.DataFrame, dept_summary: pd.DataFrame) -> None:
    _h("PeopleLens  ·  Attrition Risk Scores")

    total      = len(predictions)
    active     = (predictions["attrition"] == 0).sum()
    high_risk  = (predictions["risk_score"] >= 60).sum()
    critical   = (predictions["risk_score"] >= 80).sum()
    avg_risk   = predictions["risk_score"].mean()

    _s("COMPANY-WIDE RISK SNAPSHOT")
    print(f"  Total employees scored  : {total:,}")
    print(f"  Active employees        : {active:,}")
    print(f"  Avg risk score          : {avg_risk:.1f} / 100")
    print(f"  High-risk  (≥60)        : {_c(str(high_risk), YELLOW)}  ({high_risk/total*100:.1f}%)")
    print(f"  Critical   (≥80)        : {_c(str(critical), RED)}  ({critical/total*100:.1f}%)")

    _s("RISK TIER DISTRIBUTION")
    tier_counts = predictions["risk_tier"].value_counts().sort_index()
    for tier, count in tier_counts.items():
        pct    = count / total * 100
        colour = RED if "Critical" in str(tier) else (
                 YELLOW if "High" in str(tier) else GREEN)
        bar    = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
        print(f"  {str(tier):<12}  {_c(f'[{bar}] {count:>5,}  ({pct:4.1f}%)', colour)}")

    _s("DEPARTMENT RISK RANKING")
    print(f"  {'Department':<22}  {'Avg Risk':>9}  {'High-Risk%':>11}  {'Critical':>9}")
    print("  " + "-" * 58)
    for _, row in dept_summary.iterrows():
        colour = RED if row["avg_risk_score"] >= 60 else (
                 YELLOW if row["avg_risk_score"] >= 40 else GREEN)
        avg_rs = row["avg_risk_score"]
        hr_pct = row["high_risk_pct"]
        cr_cnt = int(row["critical_risk_count"])
        print(f"  {row['department']:<22}  "
              f"{_c(f'{avg_rs:>8.1f}', colour)}  "
              f"{hr_pct:>10.1f}%  "
              f"{cr_cnt:>9,}")

    _s("TOP 20 HIGHEST-RISK ACTIVE EMPLOYEES  (for HR intervention)")
    print("  Note: Employee IDs only — no PII exposed")
    top20 = (
        predictions[predictions["attrition"] == 0]
        .nlargest(20, "risk_score")[["employee_id", "risk_score", "risk_tier"]]
    )
    for _, row in top20.iterrows():
        colour = RED if row["risk_score"] >= 80 else YELLOW
        rs     = row["risk_score"]
        print(f"  EMP{row['employee_id']}  {_c(f'{rs:5.1f}%', colour)}  [{row['risk_tier']}]")

    print()
    print(_c("=" * W, CYAN))
    print(_c("  Predictions saved to data/processed/", GREEN + BOLD))
    print(_c("=" * W, CYAN))


# ─────────────────────────────────────────────────────────────────────────────
def run_prediction(feat: pd.DataFrame = None) -> pd.DataFrame:
    """Score every employee, build aggregated summaries, save outputs."""
    model, feature_cols = load_model()

    if feat is None:
        feat = pd.read_csv(os.path.join(PROC_DIR, "features.csv"))

    raw_emp = pd.read_csv(os.path.join(RAW_DIR, "employees.csv"))

    # Score all employees
    predictions = score_all_employees(feat, model, feature_cols)

    # Aggregated summaries
    dept_summary    = build_dept_summary(predictions, raw_emp)
    manager_summary = build_manager_summary(predictions, raw_emp)

    # Print report
    print_risk_report(predictions, dept_summary)

    # Save outputs
    os.makedirs(PROC_DIR, exist_ok=True)

    pred_path = os.path.join(PROC_DIR, "predictions.csv")
    predictions.to_csv(pred_path, index=False)
    print(f"  Saved → {pred_path}")

    dept_path = os.path.join(PROC_DIR, "dept_risk_summary.csv")
    dept_summary.to_csv(dept_path, index=False)
    print(f"  Saved → {dept_path}")

    mgr_path = os.path.join(PROC_DIR, "manager_risk_summary.csv")
    manager_summary.to_csv(mgr_path, index=False)
    print(f"  Saved → {mgr_path}")

    return predictions


if __name__ == "__main__":
    run_prediction()
