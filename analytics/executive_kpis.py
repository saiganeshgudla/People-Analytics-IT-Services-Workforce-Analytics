"""
analytics/executive_kpis.py
────────────────────────────
Computes the 3-chart executive briefing for the CHRO:
1. Headcount & Attrition KPIs
2. Department Attrition Heatmap data
3. Year-over-Year trends

These are pre-aggregated, never row-level, always k-anonymous.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from analytics.attrition_analysis import compute_attrition_by_dimension, compute_overall_attrition_kpis

log = logging.getLogger(__name__)


def compute_executive_summary(
    employees: pd.DataFrame,
    salary_df: pd.DataFrame | None = None,
    performance_df: pd.DataFrame | None = None,
) -> dict:
    """
    Compute full executive KPI summary.

    Returns:
        dict with all headline metrics for the executive dashboard.
    """
    kpis = compute_overall_attrition_kpis(employees)

    # Salary stats
    if salary_df is not None and not salary_df.empty:
        latest_salary = (
            salary_df.sort_values("effective_date")
            .groupby("employee_id")
            .last()["base_salary"]
        )
        kpis["median_salary_inr"] = float(latest_salary.median())
        kpis["avg_salary_inr"] = float(latest_salary.mean())
    else:
        kpis["median_salary_inr"] = 0.0
        kpis["avg_salary_inr"] = 0.0

    # Performance stats
    if performance_df is not None and not performance_df.empty:
        latest_perf = (
            performance_df.sort_values("review_year")
            .groupby("employee_id")
            .last()["rating"]
        )
        kpis["avg_performance_rating"] = float(latest_perf.mean())
    else:
        kpis["avg_performance_rating"] = 0.0

    # Diversity
    gender_counts = employees["gender"].value_counts(normalize=True)
    kpis["female_pct"] = float(gender_counts.get("Female", 0))
    kpis["male_pct"] = float(gender_counts.get("Male", 0))

    # College tier breakdown of attrition
    tier_attrition = compute_attrition_by_dimension(employees, "college_tier", k=10)
    kpis["tier_attrition"] = tier_attrition.to_dict(orient="records")

    return kpis


def compute_yearly_attrition_trend(employees: pd.DataFrame) -> pd.DataFrame:
    """
    Compute year-over-year voluntary attrition rate.
    """
    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    records = []
    for year in range(2019, 2025):
        # Employees active at start of year
        active_start = df[df["join_date"] <= pd.Timestamp(f"{year}-01-01")].copy()
        active_start = active_start[
            active_start["exit_date"].isna() | (active_start["exit_date"] >= pd.Timestamp(f"{year}-01-01"))
        ]
        headcount = len(active_start)

        # Who left during this year?
        left_this_year = (
            (~df["is_active"]) &
            (df["exit_date"].dt.year == year)
        ).sum()

        records.append({
            "year": year,
            "headcount": headcount,
            "attritions": int(left_this_year),
            "attrition_rate": float(left_this_year / headcount) if headcount > 0 else 0.0,
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees

    emps = generate_employees(n_total=3000, seed=42)
    summary = compute_executive_summary(emps)
    print("Executive KPIs:")
    for k, v in summary.items():
        if not isinstance(v, list):
            print(f"  {k}: {v}")

    print("\nYearly Trend:")
    trend = compute_yearly_attrition_trend(emps)
    print(trend.to_string())
