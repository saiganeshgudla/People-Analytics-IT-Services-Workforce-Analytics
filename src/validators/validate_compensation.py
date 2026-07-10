# src/validators/validate_compensation.py
"""
Validates the compensation dataset.

Checks:
  1. Salary is within defined band for each level
  2. No negative salary or bonus values
  3. Effective date is not in the future
  4. All employee_ids in compensation exist in employees master
"""

import pandas as pd


SALARY_BANDS = {
    "L1": (370_000,  550_000),
    "L2": (600_000,  950_000),
    "L3": (1_000_000, 1_500_000),
    "L4": (1_600_000, 2_400_000),
    "L5": (2_500_000, 4_500_000),
}


def validate_compensation(comp: pd.DataFrame, emp: pd.DataFrame) -> list[dict]:
    """
    Run all compensation-level validation checks.

    Args:
        comp: DataFrame loaded from compensation.csv
        emp:  DataFrame loaded from employees.csv (for referential integrity)

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # ── Check 1: No negative salary ──────────────────────────────────────────
    neg_salary = comp[comp["salary"] < 0]
    results.append({
        "name": "No Negative Salary",
        "passed": len(neg_salary) == 0,
        "detail": f"{len(neg_salary)} records with negative salary" if len(neg_salary) else "All salaries ≥ 0"
    })

    # ── Check 2: No negative bonus ───────────────────────────────────────────
    neg_bonus = comp[comp["bonus"] < 0]
    results.append({
        "name": "No Negative Bonus",
        "passed": len(neg_bonus) == 0,
        "detail": f"{len(neg_bonus)} records with negative bonus" if len(neg_bonus) else "All bonuses ≥ 0"
    })

    # ── Check 3: Salary within level band ───────────────────────────────────
    band_violations = 0
    violation_details = []
    for level, (low, high) in SALARY_BANDS.items():
        subset = comp[comp["level"] == level]
        if subset.empty:
            continue
        outside = subset[~subset["salary"].between(low, high)]
        if len(outside) > 0:
            band_violations += len(outside)
            violation_details.append(f"{level}: {len(outside)} records outside [{low:,}–{high:,}]")

    results.append({
        "name": "Salary Band Compliance",
        "passed": band_violations == 0,
        "detail": "; ".join(violation_details) if violation_details else f"All {len(SALARY_BANDS)} bands compliant"
    })

    # ── Check 4: Effective date not in future ────────────────────────────────
    comp["effective_date"] = pd.to_datetime(comp["effective_date"], errors="coerce")
    future_dates = comp[comp["effective_date"] > pd.Timestamp.today()]
    results.append({
        "name": "Effective Date (No Future)",
        "passed": len(future_dates) == 0,
        "detail": f"{len(future_dates)} future-dated records" if len(future_dates) else "All effective dates are historical"
    })

    # ── Check 5: Referential integrity – all employee IDs exist in master ────
    comp_ids = set(comp["employee_id"].unique())
    emp_ids  = set(emp["employee_id"].unique())
    orphan_ids = comp_ids - emp_ids
    results.append({
        "name": "Referential Integrity (Emp IDs)",
        "passed": len(orphan_ids) == 0,
        "detail": f"{len(orphan_ids)} unknown employee IDs in compensation" if orphan_ids else "All compensation records tied to valid employees"
    })

    return results
