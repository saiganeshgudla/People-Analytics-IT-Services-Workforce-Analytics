"""
analytics/retention_analysis.py
─────────────────────────────────
Kaplan-Meier survival analysis for new-joiner retention.
Stratified by: college tier, joining quarter, role.

Uses the `lifelines` library for KM estimation.
Privacy: cohorts with < 10 employees excluded.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

COLLEGE_TIER_LABELS = {1: "Tier 1 (IIT/NIT)", 2: "Tier 2 (State Engg)", 3: "Tier 3 (Other)"}
MIN_COHORT_SIZE = 10


def prepare_survival_data(employees: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare employee data for survival analysis.
    - duration: days from join to exit (or observation end if still active)
    - event: 1 = exited, 0 = censored (still active)
    """
    df = employees.copy()
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    observation_end = pd.Timestamp("2024-12-31")

    df["duration_days"] = (
        df["exit_date"].fillna(observation_end) - df["join_date"]
    ).dt.days
    df["event"] = (~df["is_active"]).astype(int)
    df["college_tier_label"] = df["college_tier"].map(COLLEGE_TIER_LABELS)
    df["join_year"] = df["join_date"].dt.year
    df["join_quarter"] = df["join_date"].dt.quarter
    df["join_cohort"] = df["join_year"].astype(str) + "-Q" + df["join_quarter"].astype(str)

    return df[df["duration_days"] > 0].copy()


def compute_km_by_college_tier(employees: pd.DataFrame) -> dict:
    """
    Compute Kaplan-Meier curves stratified by college tier.

    Returns:
        dict mapping tier_label → {timeline: [...], survival: [...], ci_lower, ci_upper}
    """
    try:
        from lifelines import KaplanMeierFitter
    except ImportError:
        log.warning("lifelines not installed. Run: pip install lifelines")
        return {}

    df = prepare_survival_data(employees)
    results = {}

    for tier, group in df.groupby("college_tier_label"):
        if len(group) < MIN_COHORT_SIZE:
            log.info(f"Skipping tier '{tier}' (n={len(group)} < {MIN_COHORT_SIZE})")
            continue

        kmf = KaplanMeierFitter()
        kmf.fit(
            durations=group["duration_days"],
            event_observed=group["event"],
            label=str(tier),
        )
        timeline = kmf.survival_function_.index.tolist()
        survival = kmf.survival_function_[str(tier)].tolist()
        ci_lower = kmf.confidence_interval_[f"{tier}_lower_0.95"].tolist()
        ci_upper = kmf.confidence_interval_[f"{tier}_upper_0.95"].tolist()

        results[str(tier)] = {
            "n": int(len(group)),
            "events": int(group["event"].sum()),
            "timeline": timeline,
            "survival": survival,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "median_survival_days": float(kmf.median_survival_time_),
        }

    return results


def compute_retention_cohort_table(employees: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a cohort retention table: % surviving at 6m, 12m, 24m, 36m.
    Grouped by (college_tier, join_year, join_quarter).
    """
    df = prepare_survival_data(employees)
    records = []

    for keys, group in df.groupby(["college_tier_label", "join_cohort"]):
        tier, cohort = keys
        n = len(group)
        if n < MIN_COHORT_SIZE:
            continue

        def pct_surviving(days: int) -> float:
            survived = ((group["duration_days"] >= days) | (group["event"] == 0)).sum()
            return round(survived / n, 4)

        records.append({
            "college_tier": tier,
            "join_cohort": cohort,
            "headcount": n,
            "events": int(group["event"].sum()),
            "survived_6m": pct_surviving(180),
            "survived_12m": pct_surviving(365),
            "survived_24m": pct_surviving(730),
            "survived_36m": pct_surviving(1095),
            "median_tenure_days": float(group["duration_days"].median()),
        })

    return pd.DataFrame(records).sort_values(["college_tier", "join_cohort"])


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees

    emps = generate_employees(n_total=3000, seed=42)
    table = compute_retention_cohort_table(emps)
    print(table.to_string())

    km = compute_km_by_college_tier(emps)
    for tier, data in km.items():
        print(f"\n{tier}: n={data['n']}, median survival={data['median_survival_days']:.0f} days")
