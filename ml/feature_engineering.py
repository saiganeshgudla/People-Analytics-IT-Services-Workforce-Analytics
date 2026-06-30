"""
ml/feature_engineering.py
───────────────────────────
Feature engineering for attrition prediction model.

KEY RULE: No data leakage. All features are computed from data known
at least 1 year BEFORE the prediction date. Exit events are only used
as labels, never as features.

Features used:
- Demographic: level, department, location, college_tier, gender (encoded)
- Compensation: salary_growth_rate, comp_ratio, salary_band
- Performance: avg_rating_last_2yr, rating_trend
- Tenure: tenure_days, tenure_band
- Manager: manager_attrition_history (lagged)
- Learning: avg_learning_hrs, certification_count
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def build_feature_set(
    employees: pd.DataFrame,
    salary_df: pd.DataFrame,
    performance_df: pd.DataFrame,
    learning_df: pd.DataFrame,
    prediction_date: pd.Timestamp = pd.Timestamp("2023-12-31"),
    label_window_days: int = 365,
) -> pd.DataFrame:
    """
    Build training dataset with features and labels.

    Args:
        employees: Employee master.
        salary_df: Salary history.
        performance_df: Performance ratings.
        learning_df: Learning records.
        prediction_date: The "as-of" date for feature computation.
            Features are computed from data UP TO this date.
        label_window_days: Label = did employee exit in [prediction_date, prediction_date + window]?

    Returns:
        DataFrame with features + 'label' (1 = attrited within window, 0 = retained).
    """
    cutoff = prediction_date
    label_end = prediction_date + pd.Timedelta(days=label_window_days)

    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    # Only include employees who were ACTIVE at cutoff date (i.e., hadn't left yet)
    active_at_cutoff = df[
        (df["join_date"] <= cutoff) &
        (df["exit_date"].isna() | (df["exit_date"] > cutoff))
    ].copy()

    log.info(f"Employees active at {cutoff.date()}: {len(active_at_cutoff):,}")

    # ── Label ────────────────────────────────────────────────────────────────
    # 1 if employee exited voluntarily in label window, 0 otherwise
    active_at_cutoff["label"] = (
        (~active_at_cutoff["is_active"]) &
        (active_at_cutoff["exit_date"] > cutoff) &
        (active_at_cutoff["exit_date"] <= label_end)
    ).astype(int)

    # ── Tenure features ───────────────────────────────────────────────────────
    active_at_cutoff["tenure_days"] = (cutoff - active_at_cutoff["join_date"]).dt.days
    active_at_cutoff["tenure_years"] = active_at_cutoff["tenure_days"] / 365.25

    # ── Salary features ───────────────────────────────────────────────────────
    sal = salary_df[salary_df["effective_date"] <= cutoff].copy()
    latest_salary = sal.sort_values("effective_date").groupby("employee_id").last().reset_index()
    oldest_salary = sal.sort_values("effective_date").groupby("employee_id").first().reset_index()

    salary_merged = latest_salary[["employee_id", "base_salary", "salary_band"]].rename(
        columns={"base_salary": "current_salary"}
    )
    salary_merged = salary_merged.merge(
        oldest_salary[["employee_id", "base_salary"]].rename(columns={"base_salary": "starting_salary"}),
        on="employee_id",
        how="left",
    )
    salary_merged["salary_growth_rate"] = (
        salary_merged["current_salary"] - salary_merged["starting_salary"]
    ) / salary_merged["starting_salary"].replace(0, np.nan)

    active_at_cutoff = active_at_cutoff.merge(salary_merged, on="employee_id", how="left")

    # Comp ratio (relative to peers in same role/level)
    peer_median = active_at_cutoff.groupby(["role", "level"])["current_salary"].transform("median")
    active_at_cutoff["comp_ratio"] = active_at_cutoff["current_salary"] / peer_median.replace(0, np.nan)

    # ── Performance features ───────────────────────────────────────────────────
    perf = performance_df[performance_df["review_year"] < cutoff.year].copy()
    last_2yr_perf = perf[perf["review_year"] >= cutoff.year - 2]

    avg_rating = last_2yr_perf.groupby("employee_id")["rating"].mean().rename("avg_rating_2yr")
    latest_rating = perf.sort_values("review_year").groupby("employee_id").last()["rating"].rename("latest_rating")
    oldest_rating = perf.sort_values("review_year").groupby("employee_id").first()["rating"].rename("oldest_rating")

    active_at_cutoff = active_at_cutoff.merge(avg_rating, on="employee_id", how="left")
    active_at_cutoff = active_at_cutoff.merge(latest_rating, on="employee_id", how="left")
    active_at_cutoff = active_at_cutoff.merge(oldest_rating, on="employee_id", how="left")
    active_at_cutoff["rating_trend"] = active_at_cutoff["latest_rating"] - active_at_cutoff["oldest_rating"]

    # ── Learning features ──────────────────────────────────────────────────────
    learn = learning_df[learning_df["year"] < cutoff.year].copy()
    learn_agg = learn.groupby("employee_id").agg(
        avg_learning_hrs=("learning_hours", "mean"),
        total_certifications=("certifications", "sum"),
    ).reset_index()
    active_at_cutoff = active_at_cutoff.merge(learn_agg, on="employee_id", how="left")

    # ── Categorical encoding ───────────────────────────────────────────────────
    cat_cols = ["gender", "department", "level", "location", "college_tier", "salary_band"]
    active_at_cutoff = pd.get_dummies(active_at_cutoff, columns=cat_cols, drop_first=False)

    # ── Final feature selection ────────────────────────────────────────────────
    drop_cols = [
        "join_date", "exit_date", "exit_reason", "is_active",
        "manager_id", "role",  # role has too many categories; level covers it
    ]
    feature_df = active_at_cutoff.drop(columns=drop_cols, errors="ignore")

    # Fill missing values
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    feature_df[numeric_cols] = feature_df[numeric_cols].fillna(feature_df[numeric_cols].median())

    log.info(
        f"Feature set built: {len(feature_df):,} employees, "
        f"{feature_df.shape[1]} columns, "
        f"attrition rate = {feature_df['label'].mean():.1%}"
    )
    return feature_df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    from data_generator.performance_generator import generate_performance
    from data_generator.learning_generator import generate_learning

    emps = generate_employees(n_total=2000, seed=42)
    sal = generate_salary_history(emps)
    perf = generate_performance(emps)
    learn = generate_learning(emps)

    sal["effective_date"] = pd.to_datetime(sal["effective_date"])
    features = build_feature_set(emps, sal, perf, learn)
    print(f"Feature set shape: {features.shape}")
    print(f"Label distribution:\n{features['label'].value_counts()}")
    print(features.head(3).to_string())
