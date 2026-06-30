"""
analytics/pay_fairness.py
──────────────────────────
Pay-fairness audit: comp-ratio distribution by gender / role / location.
Statistical test for disparity. Flags buckets outside ±5%.

Privacy: Only buckets with headcount >= 10 are reported.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from analytics.statistics import bootstrap_ci, welch_t_test, k_anonymity_guard

log = logging.getLogger(__name__)

DISPARITY_THRESHOLD = 0.05  # Flag if pay ratio deviates more than 5%
MIN_GROUP_SIZE = 10  # k-anonymity


def compute_comp_ratios(
    salary_df: pd.DataFrame,
    employees_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge latest salary with employee attributes and compute comp-ratio.
    Comp-ratio = actual salary / median salary for (role, level, location).

    Returns:
        DataFrame with (employee_id, gender, role, level, location, base_salary, comp_ratio)
    """
    # Latest salary per employee
    latest_salary = (
        salary_df.sort_values("effective_date")
        .groupby("employee_id")
        .last()
        .reset_index()[["employee_id", "base_salary", "salary_band"]]
    )

    merged = latest_salary.merge(
        employees_df[["employee_id", "gender", "role", "level", "location", "department"]],
        on="employee_id",
        how="inner",
    )

    # Market midpoint = median salary per (role, level, location)
    bucket_median = (
        merged.groupby(["role", "level", "location"])["base_salary"]
        .median()
        .rename("bucket_median")
        .reset_index()
    )
    merged = merged.merge(bucket_median, on=["role", "level", "location"], how="left")
    merged["comp_ratio"] = merged["base_salary"] / merged["bucket_median"]

    return merged


def compute_pay_fairness_by_gender(
    comp_df: pd.DataFrame,
    group_cols: list[str] | None = None,
    k: int = MIN_GROUP_SIZE,
) -> pd.DataFrame:
    """
    For each (role, level, location) bucket, compare pay between genders.

    Returns:
        DataFrame with pay gap metrics and disparity flags.
    """
    if group_cols is None:
        group_cols = ["role", "level", "location"]

    results = []
    for keys, group in comp_df.groupby(group_cols):
        key_dict = dict(zip(group_cols, keys if isinstance(keys, tuple) else [keys]))

        male_salaries = group[group["gender"] == "Male"]["base_salary"].values
        female_salaries = group[group["gender"] == "Female"]["base_salary"].values

        male_n = len(male_salaries)
        female_n = len(female_salaries)

        # Skip if insufficient data
        if male_n < 2 or female_n < 2 or (male_n + female_n) < k:
            continue

        male_median = float(np.median(male_salaries))
        female_median = float(np.median(female_salaries))
        gender_pay_ratio = female_median / male_median if male_median > 0 else 1.0

        # Bootstrap CI on the ratio
        def ratio_stat(data):
            m_mask = data[:male_n]
            f_mask = data[male_n:]
            return np.median(f_mask) / np.median(m_mask) if np.median(m_mask) > 0 else 1.0

        combined = np.concatenate([male_salaries, female_salaries])
        ci_lower, ci_upper = bootstrap_ci(combined, statistic=lambda x: ratio_stat(x), n_bootstrap=500)

        t_stat, p_value = welch_t_test(male_salaries, female_salaries)

        disparity_flag = abs(1 - gender_pay_ratio) > DISPARITY_THRESHOLD

        row = {
            **key_dict,
            "male_headcount": male_n,
            "female_headcount": female_n,
            "total_headcount": male_n + female_n,
            "male_median_salary": round(male_median, 0),
            "female_median_salary": round(female_median, 0),
            "gender_pay_ratio": round(gender_pay_ratio, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "t_statistic": round(t_stat, 4),
            "p_value": round(p_value, 6),
            "disparity_flag": disparity_flag,
        }
        results.append(row)

    if not results:
        log.warning("No pay fairness buckets met minimum size requirements.")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = k_anonymity_guard(df, group_cols, k=k)
    df = df.sort_values("gender_pay_ratio").reset_index(drop=True)

    flagged = df["disparity_flag"].sum()
    log.info(f"Pay fairness: {len(df)} buckets | {flagged} flagged for disparity (>{DISPARITY_THRESHOLD:.0%})")
    return df


def compute_overall_pay_fairness(comp_df: pd.DataFrame) -> dict:
    """Compute headline pay fairness KPIs."""
    male = comp_df[comp_df["gender"] == "Male"]["base_salary"]
    female = comp_df[comp_df["gender"] == "Female"]["base_salary"]

    overall_ratio = female.median() / male.median() if male.median() > 0 else 1.0

    return {
        "overall_gender_pay_ratio": round(float(overall_ratio), 4),
        "male_median_salary": round(float(male.median()), 0),
        "female_median_salary": round(float(female.median()), 0),
        "pay_gap_pct": round(float((1 - overall_ratio) * 100), 2),
        "avg_comp_ratio": round(float(comp_df["comp_ratio"].mean()), 4),
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history

    emps = generate_employees(n_total=3000, seed=42)
    sal = generate_salary_history(emps)
    comp = compute_comp_ratios(sal, emps)
    fairness = compute_pay_fairness_by_gender(comp, group_cols=["level"])
    print(fairness[["level", "total_headcount", "gender_pay_ratio", "disparity_flag"]].to_string())
    print("\nOverall:", compute_overall_pay_fairness(comp))
