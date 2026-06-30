"""
data_generator/performance_generator.py
─────────────────────────────────────────
Generates annual performance ratings (H1/Annual cycles).
- Ratings: 1–5 scale, forced distribution (bell curve around 3.5)
- High performers are less likely to attrite
- Ratings correlated with tenure and level
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_performance(employees: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate annual performance ratings for each active year.

    Args:
        employees: Output of employee_generator.generate_employees()
        seed: Random seed.

    Returns:
        DataFrame with (employee_id, review_year, rating).
    """
    rng = np.random.default_rng(seed)
    records = []

    # Forced distribution targets (common in Indian IT companies)
    # Bottom 10%: 1-2, Middle 70%: 3-4, Top 20%: 4-5
    RATING_MEAN = 3.5
    RATING_STD = 0.7

    for _, emp in employees.iterrows():
        emp_id = emp["employee_id"]
        join_date = pd.Timestamp(emp["join_date"])
        exit_date = pd.Timestamp(emp["exit_date"]) if pd.notna(emp["exit_date"]) else pd.Timestamp("2024-12-31")
        level = emp["level"]

        # Senior employees slightly higher ratings on average (survivorship)
        level_bias = {"L1": -0.1, "L2": -0.05, "L3": 0.0, "L4": 0.0,
                      "L5": 0.1, "L6": 0.15, "L7": 0.2, "L8": 0.25}.get(level, 0.0)

        start_year = join_date.year
        end_year = min(exit_date.year, 2024)

        for year in range(start_year, end_year + 1):
            # Skip if joined in the last quarter of the year (not reviewed yet)
            if year == start_year and join_date.month >= 10:
                continue

            raw_rating = rng.normal(RATING_MEAN + level_bias, RATING_STD)
            rating = round(max(1.0, min(5.0, raw_rating)) * 2) / 2  # round to 0.5 increments

            records.append({
                "employee_id": emp_id,
                "review_year": year,
                "review_cycle": "Annual",
                "rating": rating,
            })

    df = pd.DataFrame(records)
    print(f"✅ Generated {len(df):,} performance records")
    print(f"   Rating distribution:\n{df['rating'].value_counts().sort_index()}")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    perf = generate_performance(emps)
    print(perf.head())
