"""
data_generator/manager_generator.py
─────────────────────────────────────
Generates manager hierarchy records.
Managers are L5+ employees extracted from the employee master.
Adds team_size and effective_date for SCD-2 history.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_managers(employees: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Extract manager records from the employee master.

    Args:
        employees: Output of employee_generator.generate_employees()
        seed: Random seed.

    Returns:
        DataFrame with manager hierarchy records.
    """
    rng = np.random.default_rng(seed)

    MANAGER_LEVELS = ["L5", "L6", "L7", "L8"]
    managers = employees[employees["level"].isin(MANAGER_LEVELS)].copy()

    # Team size: approximate based on level
    TEAM_SIZE_BY_LEVEL = {
        "L5": (5, 12),
        "L6": (8, 18),
        "L7": (15, 35),
        "L8": (30, 80),
    }

    records = []
    for _, mgr in managers.iterrows():
        lo, hi = TEAM_SIZE_BY_LEVEL.get(mgr["level"], (5, 15))
        team_size = int(rng.integers(lo, hi + 1))

        records.append({
            "manager_id": mgr["employee_id"],
            "level": mgr["level"],
            "department": mgr["department"],
            "location": mgr["location"],
            "team_size": team_size,
            "effective_date": mgr["join_date"],
        })

    df = pd.DataFrame(records)
    df["effective_date"] = pd.to_datetime(df["effective_date"])
    print(f"✅ Generated {len(df):,} manager records")
    print(f"   Level distribution:\n{df['level'].value_counts()}")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    mgrs = generate_managers(emps)
    print(mgrs.head())
