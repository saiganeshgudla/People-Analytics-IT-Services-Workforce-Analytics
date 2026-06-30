"""
analytics/manager_effect.py
────────────────────────────
Manager-effect analysis: rolling 12-month attrition rate per manager,
benchmarked against peers at the same level, with confidence intervals.

Privacy: Only managers with team_size >= 5 are shown (k-anonymity).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from analytics.statistics import bootstrap_ci, proportion_ci

log = logging.getLogger(__name__)

MIN_TEAM_SIZE = 5  # k-anonymity guard for manager data


def compute_manager_attrition(
    employees: pd.DataFrame,
    managers: pd.DataFrame,
    reference_date: Optional[pd.Timestamp] = None,
    window_days: int = 365,
) -> pd.DataFrame:
    """
    For each manager, compute rolling 12-month attrition rate of their direct reports.
    Benchmark against peers at the same (level, department) combination.

    Args:
        employees: Employee master with manager_id column.
        managers: Manager dimension with level/dept info.
        reference_date: End of window (default: 2024-12-31).
        window_days: Rolling window in days (default: 365 = 12 months).

    Returns:
        DataFrame with manager-level attrition metrics.
    """
    if reference_date is None:
        reference_date = pd.Timestamp("2024-12-31")

    window_start = reference_date - pd.Timedelta(days=window_days)

    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    # Direct reports active during the window
    active_in_window = df[
        (df["join_date"] <= reference_date) &
        (df["exit_date"].isna() | (df["exit_date"] >= window_start))
    ].copy()

    # Who left during the window?
    active_in_window["left_in_window"] = (
        (~active_in_window["is_active"]) &
        (active_in_window["exit_date"] >= window_start) &
        (active_in_window["exit_date"] <= reference_date)
    ).astype(int)

    if active_in_window.empty or "manager_id" not in active_in_window.columns:
        log.warning("No manager data found in employees DataFrame")
        return pd.DataFrame()

    # Aggregate by manager
    mgr_stats = active_in_window.groupby("manager_id").agg(
        team_size=("employee_id", "count"),
        attritions=("left_in_window", "sum"),
        department=("department", lambda x: x.mode()[0]),
        location=("location", lambda x: x.mode()[0]),
    ).reset_index()

    mgr_stats["attrition_rate"] = mgr_stats["attritions"] / mgr_stats["team_size"]

    # Confidence intervals (Wilson score for proportions)
    ci_results = mgr_stats.apply(
        lambda row: proportion_ci(int(row["attritions"]), int(row["team_size"])),
        axis=1,
        result_type="expand",
    )
    mgr_stats["ci_lower"] = ci_results[0]
    mgr_stats["ci_upper"] = ci_results[1]

    # Join manager level info
    if not managers.empty:
        mgr_meta = managers[["manager_id", "level"]].drop_duplicates("manager_id")
        mgr_stats = mgr_stats.merge(mgr_meta, on="manager_id", how="left")

    # Peer benchmarking: average attrition rate within same (level, department)
    peer_cols = ["level", "department"] if "level" in mgr_stats.columns else ["department"]
    peer_avg = (
        mgr_stats[mgr_stats["team_size"] >= MIN_TEAM_SIZE]
        .groupby(peer_cols)["attrition_rate"]
        .mean()
        .rename("peer_avg_attrition")
        .reset_index()
    )
    mgr_stats = mgr_stats.merge(peer_avg, on=peer_cols, how="left")
    mgr_stats["attrition_vs_peers"] = mgr_stats["attrition_rate"] - mgr_stats["peer_avg_attrition"]
    mgr_stats["risk_flag"] = mgr_stats["attrition_rate"] > (mgr_stats["peer_avg_attrition"] + 0.10)

    # Apply k-anonymity
    mgr_stats = mgr_stats[mgr_stats["team_size"] >= MIN_TEAM_SIZE].copy()
    mgr_stats = mgr_stats.sort_values("attrition_rate", ascending=False).reset_index(drop=True)

    log.info(f"Manager effect: {len(mgr_stats)} managers analysed, {mgr_stats['risk_flag'].sum()} flagged")
    return mgr_stats


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees
    from data_generator.manager_generator import generate_managers

    emps = generate_employees(n_total=2000, seed=42)
    mgrs = generate_managers(emps)
    result = compute_manager_attrition(emps, mgrs)
    print(result[["manager_id", "team_size", "attrition_rate", "peer_avg_attrition", "risk_flag"]].head(15).to_string())
