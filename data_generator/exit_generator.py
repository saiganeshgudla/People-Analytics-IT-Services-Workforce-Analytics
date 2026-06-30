"""
data_generator/exit_generator.py
──────────────────────────────────
Generates exit interview records for employees who left NimbusTech.
Derived from the employee master — no new randomness needed for core fields,
but adds voluntary/involuntary split and derived tenure fields.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_exits(employees: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate exit records for all employees with an exit_date.

    Args:
        employees: Output of employee_generator.generate_employees()
        seed: Random seed.

    Returns:
        DataFrame with one row per exited employee.
    """
    rng = np.random.default_rng(seed)

    exited = employees[employees["is_active"] == False].copy()

    if exited.empty:
        print("⚠️  No exited employees found.")
        return pd.DataFrame()

    # 90% voluntary in IT services (Better Opportunity / Pay)
    exited["voluntary"] = rng.random(len(exited)) < 0.90

    exited["join_date"] = pd.to_datetime(exited["join_date"])
    exited["exit_date"] = pd.to_datetime(exited["exit_date"])
    exited["tenure_days"] = (exited["exit_date"] - exited["join_date"]).dt.days

    df = exited[[
        "employee_id", "exit_date", "exit_reason", "manager_id",
        "tenure_days", "voluntary",
    ]].rename(columns={"manager_id": "last_manager_id"})

    df["exit_date"] = df["exit_date"].dt.date

    print(f"✅ Generated {len(df):,} exit records")
    print(f"   Voluntary: {df['voluntary'].mean():.1%} | Top reason: {df['exit_reason'].mode()[0]}")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    exits = generate_exits(emps)
    print(exits["exit_reason"].value_counts())
