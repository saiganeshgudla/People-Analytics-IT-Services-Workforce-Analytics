"""
analytics/attrition_analysis.py
─────────────────────────────────
Computes attrition rates by department, location, level, tenure band.
Privacy-preserving: k-anonymity applied before output.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from analytics.statistics import bootstrap_ci, k_anonymity_guard

log = logging.getLogger(__name__)


def compute_attrition_by_dimension(
    employees: pd.DataFrame,
    dimension: str,
    k: int = 10,
) -> pd.DataFrame:
    """
    Compute voluntary attrition rate for a given demographic dimension.

    Args:
        employees: Employee master DataFrame.
        dimension: Column name to group by (e.g., 'department', 'location', 'level').
        k: Minimum group size for k-anonymity.

    Returns:
        DataFrame with columns [dimension, headcount, attrited, attrition_rate, ci_lower, ci_upper]
    """
    df = employees.copy()
    df["attrited"] = (~df["is_active"]).astype(int)

    grouped = df.groupby(dimension).agg(
        headcount=("employee_id", "count"),
        attrited=("attrited", "sum"),
    ).reset_index()

    grouped["attrition_rate"] = grouped["attrited"] / grouped["headcount"]

    # Bootstrap CI for each group
    ci_rows = []
    for _, row in grouped.iterrows():
        group_data = df[df[dimension] == row[dimension]]["attrited"].values
        lo, hi = bootstrap_ci(group_data, statistic=np.mean, n_bootstrap=500)
        ci_rows.append({"ci_lower": lo, "ci_upper": hi})

    grouped = pd.concat([grouped, pd.DataFrame(ci_rows)], axis=1)
    grouped = k_anonymity_guard(grouped, [dimension], k=k)
    grouped = grouped.sort_values("attrition_rate", ascending=False).reset_index(drop=True)

    log.info(f"Attrition by {dimension}: {len(grouped)} groups computed")
    return grouped


def compute_tenure_attrition_bands(employees: pd.DataFrame) -> pd.DataFrame:
    """
    Compute attrition rates in tenure bands: <6m, 6-12m, 1-2yr, 2-3yr, 3+yr.
    Critical for identifying Year-1 attrition crisis.
    """
    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    df["tenure_days"] = (
        df["exit_date"].fillna(pd.Timestamp("2024-12-31")) - df["join_date"]
    ).dt.days

    df["tenure_band"] = pd.cut(
        df["tenure_days"],
        bins=[0, 180, 365, 730, 1095, 99999],
        labels=["<6 months", "6–12 months", "1–2 years", "2–3 years", "3+ years"],
    )

    grouped = df.groupby("tenure_band", observed=True).agg(
        headcount=("employee_id", "count"),
        attrited=("is_active", lambda x: (~x).sum()),
    ).reset_index()

    grouped["attrition_rate"] = grouped["attrited"] / grouped["headcount"]
    return grouped


def compute_overall_attrition_kpis(employees: pd.DataFrame) -> dict:
    """Compute headline KPIs for the executive summary."""
    total = len(employees)
    exited = (~employees["is_active"]).sum()
    voluntary = employees[~employees["is_active"]]["exit_reason"].notna().sum()

    # Year-1 attrition for new joiners
    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    df["tenure_days"] = (df["exit_date"].fillna(pd.Timestamp("2024-12-31")) - df["join_date"]).dt.days

    year_1_left = ((~df["is_active"]) & (df["tenure_days"] <= 365)).sum()
    total_new_joiners = (df["join_date"].dt.year >= 2023).sum()
    year_1_attrition = year_1_left / total if total > 0 else 0

    return {
        "total_headcount": int(total),
        "active_employees": int(total - exited),
        "exited_employees": int(exited),
        "overall_attrition_rate": float(exited / total),
        "voluntary_attrition_rate": float(voluntary / total),
        "year_1_attrition_rate": float(year_1_attrition),
        "new_joiners_12m": int(total_new_joiners),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees

    emps = generate_employees(n_total=2000, seed=42)
    print("── Attrition by Department ──")
    print(compute_attrition_by_dimension(emps, "department").to_string())
    print("\n── Attrition by Tenure Band ──")
    print(compute_tenure_attrition_bands(emps).to_string())
    print("\n── Overall KPIs ──")
    print(compute_overall_attrition_kpis(emps))
