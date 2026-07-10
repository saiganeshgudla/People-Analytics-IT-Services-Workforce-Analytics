# src/validators/validate_performance.py
"""
Validates the performance (appraisal) dataset.

Checks:
  1. Performance rating is within 1–5
  2. Review year is not in the future
  3. All employee_ids exist in employees master
  4. Promotion column contains only allowed values
"""

import pandas as pd


ALLOWED_PROMOTIONS = {"Yes", "No"}
CURRENT_YEAR = pd.Timestamp.today().year


def validate_performance(perf: pd.DataFrame, emp: pd.DataFrame) -> list[dict]:
    """
    Run all performance-level validation checks.

    Args:
        perf: DataFrame loaded from performance.csv
        emp:  DataFrame loaded from employees.csv (for referential integrity)

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # ── Check 1: Rating within [1, 5] ───────────────────────────────────────
    invalid_ratings = perf[~perf["rating"].between(1, 5)]
    results.append({
        "name": "Performance Rating (1–5)",
        "passed": len(invalid_ratings) == 0,
        "detail": f"{len(invalid_ratings)} out-of-range ratings" if len(invalid_ratings) else "All ratings within [1, 5]"
    })

    # ── Check 2: Review year not in future ──────────────────────────────────
    future_years = perf[perf["review_year"] > CURRENT_YEAR]
    results.append({
        "name": "Review Year (No Future)",
        "passed": len(future_years) == 0,
        "detail": f"{len(future_years)} records with future review year" if len(future_years) else f"All review years ≤ {CURRENT_YEAR}"
    })

    # ── Check 3: Referential integrity ──────────────────────────────────────
    perf_ids = set(perf["employee_id"].unique())
    emp_ids  = set(emp["employee_id"].unique())
    orphan_ids = perf_ids - emp_ids
    results.append({
        "name": "Referential Integrity (Emp IDs)",
        "passed": len(orphan_ids) == 0,
        "detail": f"{len(orphan_ids)} unknown employee IDs in performance" if orphan_ids else "All performance records tied to valid employees"
    })

    # ── Check 4: Promotion values ────────────────────────────────────────────
    invalid_promo = perf[~perf["promotion"].isin(ALLOWED_PROMOTIONS)]
    results.append({
        "name": "Promotion Values (Yes/No)",
        "passed": len(invalid_promo) == 0,
        "detail": f"Invalid values: {invalid_promo['promotion'].unique().tolist()}" if len(invalid_promo) else "All promotion flags are Yes/No"
    })

    return results
