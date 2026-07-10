# src/ml/feature_engineering.py
"""
Feature Engineering for Attrition Prediction
==============================================
Converts raw HR tables into a structured feature matrix.

Features built:
  Demographic   : age, gender (encoded), college_tier (encoded)
  Organisational: department, level, location (encoded)
  Tenure        : tenure_months (derived from joining_date)
  Compensation  : latest salary, latest bonus, salary_growth_pct
  Performance   : latest rating, avg rating, rating trend (last - first)
  Career        : promotion_count, promotion_rate
  Learning      : total hours completed, courses taken
  Workload      : project count, billable project ratio
  Target        : attrition  (0 = Active, 1 = Exited)

Output: data/processed/features.csv

Run:
    python -m src.ml.feature_engineering
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

RAW_DIR  = os.path.join(ROOT, "data", "synthetic")
PROC_DIR = os.path.join(ROOT, "data", "processed")
TODAY    = pd.Timestamp("2026-07-10")          # fixed reference date for reproducibility


# ─────────────────────────────────────────────────────────────────────────────
def load_raw() -> dict:
    files = {
        "employees":   "employees.csv",
        "performance": "performance.csv",
        "comp":        "compensation.csv",
        "learning":    "learning.csv",
        "projects":    "project_assignments.csv",
        "exits":       "exit_records.csv",
    }
    return {k: pd.read_csv(os.path.join(RAW_DIR, v)) for k, v in files.items()}


# ─────────────────────────────────────────────────────────────────────────────
def build_features(raw: dict) -> pd.DataFrame:
    emp   = raw["employees"].copy()
    perf  = raw["performance"].copy()
    comp  = raw["comp"].copy()
    learn = raw["learning"].copy()
    proj  = raw["projects"].copy()
    exits = raw["exits"].copy()

    emp["joining_date"] = pd.to_datetime(emp["joining_date"], errors="coerce")
    exits["exit_date"]  = pd.to_datetime(exits["exit_date"],  errors="coerce")
    comp["effective_date"] = pd.to_datetime(comp["effective_date"], errors="coerce")

    # ── Target variable ───────────────────────────────────────────────────────
    emp["attrition"] = (emp["status"] == "Exited").astype(int)

    # ── F1: Tenure in months (up to exit_date for exited; up to TODAY for active) ──
    emp = emp.merge(exits[["employee_id", "exit_date"]], on="employee_id", how="left")
    emp["end_date"]      = emp["exit_date"].fillna(TODAY)
    emp["tenure_months"] = ((emp["end_date"] - emp["joining_date"]).dt.days / 30.44).round(2)
    emp["joining_year"]  = emp["joining_date"].dt.year
    emp["joining_month"] = emp["joining_date"].dt.month

    # ── F2: Compensation features ─────────────────────────────────────────────
    comp_sorted = comp.sort_values("effective_date")

    latest_comp = (
        comp_sorted.groupby("employee_id").last().reset_index()
        [["employee_id", "salary", "bonus", "stock"]]
        .rename(columns={"salary": "latest_salary", "bonus": "latest_bonus",
                          "stock": "latest_stock"})
    )
    # Salary growth: last salary - first salary / first salary
    first_comp  = comp_sorted.groupby("employee_id").first().reset_index()[["employee_id", "salary"]]
    last_comp   = comp_sorted.groupby("employee_id").last().reset_index()[["employee_id", "salary"]]
    salary_growth = first_comp.merge(last_comp, on="employee_id", suffixes=("_first", "_last"))
    salary_growth["salary_growth_pct"] = (
        (salary_growth["salary_last"] - salary_growth["salary_first"])
        / salary_growth["salary_first"].replace(0, np.nan) * 100
    ).round(2).fillna(0)

    emp = emp.merge(latest_comp, on="employee_id", how="left")
    emp = emp.merge(salary_growth[["employee_id", "salary_growth_pct"]], on="employee_id", how="left")

    # ── F3: Performance features ──────────────────────────────────────────────
    perf_sorted = perf.sort_values("review_year")

    avg_rating   = perf.groupby("employee_id")["rating"].mean().round(2).reset_index(name="avg_rating")
    latest_perf  = perf_sorted.groupby("employee_id").last().reset_index()[["employee_id", "rating"]].rename(columns={"rating": "latest_rating"})
    first_rating = perf_sorted.groupby("employee_id").first().reset_index()[["employee_id", "rating"]].rename(columns={"rating": "first_rating"})

    rating_trend = latest_perf.merge(first_rating, on="employee_id")
    rating_trend["rating_trend"] = (rating_trend["latest_rating"] - rating_trend["first_rating"]).round(2)

    emp = emp.merge(avg_rating,  on="employee_id", how="left")
    emp = emp.merge(latest_perf, on="employee_id", how="left")
    emp = emp.merge(rating_trend[["employee_id", "rating_trend"]], on="employee_id", how="left")

    # ── F4: Career growth features ────────────────────────────────────────────
    promo_count = (
        perf.groupby("employee_id")["promotion"]
        .apply(lambda x: (x == "Yes").sum())
        .reset_index(name="promotion_count")
    )
    total_reviews = perf.groupby("employee_id").size().reset_index(name="review_count")
    promo_data = promo_count.merge(total_reviews, on="employee_id")
    promo_data["promotion_rate"] = (
        promo_data["promotion_count"] / promo_data["review_count"].replace(0, np.nan)
    ).round(3).fillna(0)

    emp = emp.merge(promo_data[["employee_id", "promotion_count", "promotion_rate"]], on="employee_id", how="left")

    # ── F5: Learning features ─────────────────────────────────────────────────
    learn_agg = learn.groupby("employee_id").agg(
        total_learning_hours=("hours_completed", "sum"),
        courses_taken=("course_name", "count"),
        completed_courses=("completion_status", lambda x: (x == "Completed").sum()),
    ).reset_index()
    learn_agg["completion_rate"] = (
        learn_agg["completed_courses"] / learn_agg["courses_taken"].replace(0, np.nan)
    ).round(3).fillna(0)

    emp = emp.merge(learn_agg[["employee_id", "total_learning_hours", "courses_taken",
                                "completion_rate"]], on="employee_id", how="left")
    emp["total_learning_hours"] = emp["total_learning_hours"].fillna(0)
    emp["courses_taken"]        = emp["courses_taken"].fillna(0)
    emp["completion_rate"]      = emp["completion_rate"].fillna(0)

    # ── F6: Project / workload features ───────────────────────────────────────
    proj_agg = proj.groupby("employee_id").agg(
        project_count=("project_name", "count"),
        billable_projects=("billable", lambda x: (x == True).sum() + (x == "Yes").sum()),
    ).reset_index()
    proj_agg["billable_ratio"] = (
        proj_agg["billable_projects"] / proj_agg["project_count"].replace(0, np.nan)
    ).round(3).fillna(0)

    emp = emp.merge(proj_agg[["employee_id", "project_count", "billable_ratio"]],
                    on="employee_id", how="left")
    emp["project_count"] = emp["project_count"].fillna(0)
    emp["billable_ratio"] = emp["billable_ratio"].fillna(0)

    # ── F7: Manager experience (from managers table if available) ─────────────
    mgr_path = os.path.join(RAW_DIR, "managers.csv")
    if os.path.exists(mgr_path):
        mgr = pd.read_csv(mgr_path)[["manager_id", "experience_years"]]
        emp = emp.merge(mgr, on="manager_id", how="left")
        emp["manager_experience_years"] = emp["experience_years"].fillna(
            emp["experience_years"].median()
        )
        emp.drop(columns=["experience_years"], inplace=True)
    else:
        emp["manager_experience_years"] = 0

    # ── Encode categoricals with pd.get_dummies ───────────────────────────────
    cat_cols = ["gender", "department", "location", "level", "college_tier"]
    emp = pd.get_dummies(emp, columns=cat_cols, drop_first=False, dtype=int)

    # ── Drop columns not used as features ─────────────────────────────────────
    drop_cols = [
        "status", "joining_date", "exit_date", "end_date",
        "role",           # 45 cardinality — too noisy; department captures it
        "manager_id",
    ]
    emp.drop(columns=[c for c in drop_cols if c in emp.columns], inplace=True)

    # Fill remaining NaNs with median
    num_cols = emp.select_dtypes(include=[np.number]).columns
    emp[num_cols] = emp[num_cols].fillna(emp[num_cols].median())

    print(f"  Feature matrix shape : {emp.shape}")
    print(f"  Attrition rate       : {emp['attrition'].mean()*100:.2f}%")
    print(f"  Features             : {emp.shape[1] - 3} predictors")   # minus employee_id, joining_year, attrition
    return emp


# ─────────────────────────────────────────────────────────────────────────────
def run_feature_engineering() -> pd.DataFrame:
    print("Building feature matrix…")
    raw  = load_raw()
    feat = build_features(raw)
    os.makedirs(PROC_DIR, exist_ok=True)
    out  = os.path.join(PROC_DIR, "features.csv")
    feat.to_csv(out, index=False)
    print(f"  Saved → {out}")
    return feat


if __name__ == "__main__":
    run_feature_engineering()
