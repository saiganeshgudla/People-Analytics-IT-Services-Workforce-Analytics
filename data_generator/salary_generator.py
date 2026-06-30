"""
data_generator/salary_generator.py
────────────────────────────────────
Generates compensation history for NimbusTech employees.
- Salary bands by level: realistic INR ranges
- Annual increments: 8-18% depending on performance
- Gender pay gap simulation: ~7% gap at entry level, closes with seniority
- Multiple salary records per employee (annual review history)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ── Salary Bands (Annual, INR) ─────────────────────────────────────────────────
SALARY_BANDS: dict[str, dict] = {
    "L1": {"min": 350_000,  "mid": 450_000,  "max": 600_000,  "band": "B1"},
    "L2": {"min": 550_000,  "mid": 700_000,  "max": 900_000,  "band": "B2"},
    "L3": {"min": 800_000,  "mid": 1_050_000,"max": 1_400_000,"band": "B3"},
    "L4": {"min": 1_200_000,"mid": 1_600_000,"max": 2_200_000,"band": "B4"},
    "L5": {"min": 1_800_000,"mid": 2_400_000,"max": 3_200_000,"band": "B5"},
    "L6": {"min": 2_800_000,"mid": 3_800_000,"max": 5_000_000,"band": "B6"},
    "L7": {"min": 4_500_000,"mid": 6_000_000,"max": 8_000_000,"band": "B7"},
    "L8": {"min": 7_000_000,"mid": 9_500_000,"max": 13_000_000,"band": "B8"},
}

# Gender pay gap by level (% below market for female, shrinks with seniority)
GENDER_GAP: dict[str, float] = {
    "L1": 0.07, "L2": 0.06, "L3": 0.05, "L4": 0.04,
    "L5": 0.03, "L6": 0.02, "L7": 0.01, "L8": 0.005,
}


def _starting_salary(level: str, gender: str, rng: np.random.Generator) -> float:
    """Draw starting salary from band distribution with gender adjustment."""
    band = SALARY_BANDS[level]
    # Log-normal distribution centered at midpoint
    log_mid = np.log(band["mid"])
    log_std = 0.12
    salary = float(np.exp(rng.normal(log_mid, log_std)))
    salary = max(band["min"], min(band["max"], salary))

    # Apply gender gap (simulates real-world structural gap)
    if gender == "Female":
        gap = GENDER_GAP.get(level, 0.03)
        salary *= (1 - gap * rng.uniform(0.5, 1.5))

    return round(salary, -2)  # round to nearest 100


def generate_salary_history(employees: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate annual salary history for all employees.

    Args:
        employees: Output of employee_generator.generate_employees()
        seed: Random seed.

    Returns:
        DataFrame with one row per employee per year they were active.
    """
    rng = np.random.default_rng(seed)
    records = []

    for _, emp in employees.iterrows():
        emp_id = emp["employee_id"]
        level = emp["level"]
        gender = emp["gender"]
        join_date = pd.Timestamp(emp["join_date"])
        exit_date = pd.Timestamp(emp["exit_date"]) if pd.notna(emp["exit_date"]) else pd.Timestamp("2024-12-31")

        # Starting salary at join date
        current_salary = _starting_salary(level, gender, rng)
        effective_date = join_date

        # Record for each April (typical salary revision in Indian IT)
        # First record is at joining
        records.append({
            "employee_id": emp_id,
            "effective_date": effective_date.date(),
            "base_salary": current_salary,
            "salary_band": SALARY_BANDS[level]["band"],
        })

        # Annual revisions every April
        year = join_date.year + 1
        while True:
            revision_date = pd.Timestamp(f"{year}-04-01")
            if revision_date > exit_date or revision_date > pd.Timestamp("2024-12-31"):
                break

            # Increment: 8-18% based on performance (approximate)
            # High performers (simulated by ~20% of employees) get 15-18%
            is_high_performer = rng.random() < 0.20
            if is_high_performer:
                increment_pct = rng.uniform(0.14, 0.18)
            else:
                increment_pct = rng.uniform(0.08, 0.13)

            current_salary = round(current_salary * (1 + increment_pct), -2)
            band = SALARY_BANDS[level]
            current_salary = min(current_salary, band["max"])

            records.append({
                "employee_id": emp_id,
                "effective_date": revision_date.date(),
                "base_salary": current_salary,
                "salary_band": band["band"],
            })
            year += 1

    df = pd.DataFrame(records)
    df["effective_date"] = pd.to_datetime(df["effective_date"])
    print(f"✅ Generated {len(df):,} salary records for {employees['employee_id'].nunique():,} employees")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    sal = generate_salary_history(emps)
    print(sal.groupby("salary_band")["base_salary"].describe())
