# src/validators/validate_learning.py
"""
Validates the learning (L&D) dataset.

Checks:
  1. hours_completed >= 0 (no negative learning hours)
  2. completion_status contains only allowed values
  3. completion_date is not in the future
  4. All employee_ids exist in employees master
"""

import pandas as pd


ALLOWED_STATUSES = {"Completed", "In Progress", "Not Started"}


def validate_learning(learn: pd.DataFrame, emp: pd.DataFrame) -> list[dict]:
    """
    Run all learning-record-level validation checks.

    Args:
        learn: DataFrame loaded from learning.csv
        emp:   DataFrame loaded from employees.csv (for referential integrity)

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # ── Check 1: Non-negative learning hours ─────────────────────────────────
    neg_hours = learn[learn["hours_completed"] < 0]
    results.append({
        "name": "Learning Hours (≥ 0)",
        "passed": len(neg_hours) == 0,
        "detail": f"{len(neg_hours)} records with negative hours" if len(neg_hours) else "All learning hours are non-negative"
    })

    # ── Check 2: Completion status values ────────────────────────────────────
    invalid_status = learn[~learn["completion_status"].isin(ALLOWED_STATUSES)]
    results.append({
        "name": "Completion Status Values",
        "passed": len(invalid_status) == 0,
        "detail": f"Invalid values: {invalid_status['completion_status'].unique().tolist()}" if len(invalid_status) else f"All statuses within {ALLOWED_STATUSES}"
    })

    # ── Check 3: Completion date not in future ────────────────────────────────
    learn = learn.copy()
    learn["completion_date"] = pd.to_datetime(learn["completion_date"], errors="coerce")
    # Only check rows that have a completion date (Completed status)
    completed = learn.dropna(subset=["completion_date"])
    future_completions = completed[completed["completion_date"] > pd.Timestamp.today()]
    results.append({
        "name": "Completion Date (No Future)",
        "passed": len(future_completions) == 0,
        "detail": f"{len(future_completions)} future completion dates" if len(future_completions) else "All completion dates are historical"
    })

    # ── Check 4: Referential integrity ───────────────────────────────────────
    learn_ids = set(learn["employee_id"].unique())
    emp_ids   = set(emp["employee_id"].unique())
    orphan_ids = learn_ids - emp_ids
    results.append({
        "name": "Referential Integrity (Emp IDs)",
        "passed": len(orphan_ids) == 0,
        "detail": f"{len(orphan_ids)} unknown employee IDs in learning" if orphan_ids else "All learning records tied to valid employees"
    })

    return results
