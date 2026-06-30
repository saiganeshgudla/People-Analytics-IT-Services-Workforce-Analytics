"""
data_generator/learning_generator.py
──────────────────────────────────────
Generates quarterly learning hours and certification counts.
- Average 40 hrs/quarter for active employees
- Higher performers spend more time on learning
- Certifications: 0-3 per year depending on level
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_learning(employees: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate quarterly learning records for all employees.

    Args:
        employees: Output of employee_generator.generate_employees()
        seed: Random seed.

    Returns:
        DataFrame with (employee_id, year, quarter, learning_hours, certifications)
    """
    rng = np.random.default_rng(seed)
    records = []

    LEVEL_LEARNING_MEAN = {
        "L1": 50, "L2": 45, "L3": 40, "L4": 38, "L5": 35, "L6": 32, "L7": 28, "L8": 25
    }

    for _, emp in employees.iterrows():
        emp_id = emp["employee_id"]
        join_date = pd.Timestamp(emp["join_date"])
        exit_date = pd.Timestamp(emp["exit_date"]) if pd.notna(emp["exit_date"]) else pd.Timestamp("2024-12-31")
        level = emp["level"]

        base_hours = LEVEL_LEARNING_MEAN.get(level, 40)

        current = join_date
        while current < exit_date and current.year <= 2024:
            q = (current.month - 1) // 3 + 1
            # Learning hours ~ Poisson(base) with noise
            hours = float(rng.poisson(base_hours) + rng.normal(0, 5))
            hours = max(0, round(hours, 1))

            # Certifications: mostly 0, sometimes 1, rarely 2+
            certs = int(rng.choice([0, 1, 2, 3], p=[0.70, 0.22, 0.06, 0.02]))

            records.append({
                "employee_id": emp_id,
                "year": current.year,
                "quarter": q,
                "learning_hours": hours,
                "certifications": certs,
            })

            # Advance by one quarter
            month = current.month + 3
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            try:
                current = pd.Timestamp(f"{year}-{month:02d}-01")
            except Exception:
                break

    df = pd.DataFrame(records)
    print(f"✅ Generated {len(df):,} learning records")
    print(f"   Avg learning hours/quarter: {df['learning_hours'].mean():.1f}")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    learn = generate_learning(emps)
    print(learn.head())
