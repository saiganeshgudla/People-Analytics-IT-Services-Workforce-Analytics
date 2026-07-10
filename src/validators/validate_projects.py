# src/validators/validate_projects.py
"""
Validates the project assignments dataset.

Checks:
  1. No duplicate rows (composite uniqueness)
  2. end_date >= start_date (no negative duration projects)
  3. start_date is not in the future
  4. Billable column contains only allowed values
  5. All employee_ids exist in employees master
"""

import pandas as pd


ALLOWED_BILLABLE = {"Yes", "No", True, False}


def validate_projects(proj: pd.DataFrame, emp: pd.DataFrame) -> list[dict]:
    """
    Run all project-assignment-level validation checks.

    Args:
        proj: DataFrame loaded from project_assignments.csv
        emp:  DataFrame loaded from employees.csv (for referential integrity)

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # Parse dates once for all checks
    proj = proj.copy()
    proj["start_date"] = pd.to_datetime(proj["start_date"], errors="coerce")
    proj["end_date"]   = pd.to_datetime(proj["end_date"],   errors="coerce")

    # ── Check 1: No fully duplicate rows ─────────────────────────────────────
    dup_rows = proj.duplicated().sum()
    results.append({
        "name": "No Duplicate Assignment Rows",
        "passed": dup_rows == 0,
        "detail": f"{dup_rows} fully duplicate rows found" if dup_rows else f"{len(proj)} rows – no duplicates"
    })

    # ── Check 2: end_date >= start_date ──────────────────────────────────────
    invalid_dates = proj[proj["end_date"] < proj["start_date"]]
    results.append({
        "name": "Project Date Order (end ≥ start)",
        "passed": len(invalid_dates) == 0,
        "detail": f"{len(invalid_dates)} projects with end_date < start_date" if len(invalid_dates) else "All project dates are logically ordered"
    })

    # ── Check 3: start_date not in future ────────────────────────────────────
    future_starts = proj[proj["start_date"] > pd.Timestamp.today()]
    results.append({
        "name": "Project Start Date (No Future)",
        "passed": len(future_starts) == 0,
        "detail": f"{len(future_starts)} projects with future start_date" if len(future_starts) else "All project start dates are historical"
    })

    # ── Check 4: Billable values ──────────────────────────────────────────────
    invalid_billable = proj[~proj["billable"].isin(ALLOWED_BILLABLE)]
    results.append({
        "name": "Billable Flag (Yes/No/Bool)",
        "passed": len(invalid_billable) == 0,
        "detail": f"Invalid values: {invalid_billable['billable'].unique().tolist()}" if len(invalid_billable) else "All billable flags are valid (Yes/No or True/False)"
    })

    # ── Check 5: Referential integrity ───────────────────────────────────────
    proj_ids = set(proj["employee_id"].unique())
    emp_ids  = set(emp["employee_id"].unique())
    orphan_ids = proj_ids - emp_ids
    results.append({
        "name": "Referential Integrity (Emp IDs)",
        "passed": len(orphan_ids) == 0,
        "detail": f"{len(orphan_ids)} unknown employee IDs in projects" if orphan_ids else "All project records tied to valid employees"
    })

    return results
