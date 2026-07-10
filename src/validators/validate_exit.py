# src/validators/validate_exit.py
"""
Validates the exit records dataset.

Checks:
  1. exit_date >= joining_date (cannot exit before joining)
  2. exit_date is not in the future
  3. exit_reason is not null / blank
  4. voluntary column contains only True/False
  5. All employee_ids in exits actually exist in employees master
"""

import pandas as pd


def validate_exit(exits: pd.DataFrame, emp: pd.DataFrame) -> list[dict]:
    """
    Run all exit-record-level validation checks.

    Args:
        exits: DataFrame loaded from exit_records.csv
        emp:   DataFrame loaded from employees.csv (for referential integrity
               and joining-date comparison)

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # Merge exit records with employee joining dates for date comparison
    exits = exits.copy()
    exits["exit_date"] = pd.to_datetime(exits["exit_date"], errors="coerce")

    emp_dates = emp[["employee_id", "joining_date"]].copy()
    emp_dates["joining_date"] = pd.to_datetime(emp_dates["joining_date"], errors="coerce")

    merged = exits.merge(emp_dates, on="employee_id", how="left")

    # ── Check 1: Referential integrity – exit records must have valid emp ID ─
    exit_ids = set(exits["employee_id"].unique())
    emp_ids  = set(emp["employee_id"].unique())
    orphan_ids = exit_ids - emp_ids
    results.append({
        "name": "Referential Integrity (Emp IDs)",
        "passed": len(orphan_ids) == 0,
        "detail": f"{len(orphan_ids)} unknown employee IDs in exits" if orphan_ids else "All exit records tied to valid employees"
    })

    # ── Check 2: exit_date >= joining_date ───────────────────────────────────
    invalid_exit_dates = merged[merged["exit_date"] < merged["joining_date"]]
    results.append({
        "name": "Exit Date After Joining Date",
        "passed": len(invalid_exit_dates) == 0,
        "detail": f"{len(invalid_exit_dates)} exits before joining date" if len(invalid_exit_dates) else "All exit dates are after corresponding joining dates"
    })

    # ── Check 3: exit_date not in future ─────────────────────────────────────
    future_exits = exits[exits["exit_date"] > pd.Timestamp.today()]
    results.append({
        "name": "Exit Date (No Future)",
        "passed": len(future_exits) == 0,
        "detail": f"{len(future_exits)} future-dated exits" if len(future_exits) else "All exit dates are historical"
    })

    # ── Check 4: exit_reason not blank ───────────────────────────────────────
    blank_reasons = exits[exits["exit_reason"].isnull() | (exits["exit_reason"].str.strip() == "")]
    results.append({
        "name": "Exit Reason Not Blank",
        "passed": len(blank_reasons) == 0,
        "detail": f"{len(blank_reasons)} records with blank exit_reason" if len(blank_reasons) else "All exit records have a reason"
    })

    # ── Check 5: voluntary is boolean-compatible ──────────────────────────────
    valid_voluntary = exits["voluntary"].isin([True, False, "True", "False", 1, 0])
    invalid_voluntary = exits[~valid_voluntary]
    results.append({
        "name": "Voluntary Flag (Boolean)",
        "passed": len(invalid_voluntary) == 0,
        "detail": f"{len(invalid_voluntary)} records with invalid voluntary flag" if len(invalid_voluntary) else "All voluntary flags are boolean"
    })

    return results
