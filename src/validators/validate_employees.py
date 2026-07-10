# src/validators/validate_employees.py
"""
Validates the core employees dataset.

Checks:
  1. Employee IDs are unique (primary key integrity)
  2. Age is within realistic working range (21–60)
  3. Gender values are within allowed categories
  4. Joining dates are not in the future
  5. No null values in critical columns
"""

import pandas as pd


REQUIRED_COLUMNS = [
    "employee_id", "gender", "age", "location",
    "department", "role", "level", "joining_date",
    "college_tier", "manager_id", "status"
]

ALLOWED_GENDERS = {"Male", "Female", "Other", "Non-binary"}
ALLOWED_STATUSES = {"Active", "Inactive", "Exited"}


def validate_employees(emp: pd.DataFrame) -> list[dict]:
    """
    Run all employee-level validation checks.

    Args:
        emp: DataFrame loaded from employees.csv

    Returns:
        List of result dicts with keys: name, passed, detail
    """
    results = []

    # ── Check 1: Schema – required columns present ──────────────────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in emp.columns]
    results.append({
        "name": "Employee Schema",
        "passed": len(missing_cols) == 0,
        "detail": f"Missing columns: {missing_cols}" if missing_cols else f"{len(REQUIRED_COLUMNS)} required columns present"
    })

    # ── Check 2: Employee ID uniqueness ─────────────────────────────────────
    dup_count = emp["employee_id"].duplicated().sum()
    results.append({
        "name": "Employee ID Uniqueness",
        "passed": emp["employee_id"].is_unique,
        "detail": f"Duplicate IDs found: {dup_count}" if dup_count else f"{len(emp)} unique IDs confirmed"
    })

    # ── Check 3: No nulls in critical columns ────────────────────────────────
    null_counts = emp[REQUIRED_COLUMNS].isnull().sum()
    has_nulls = null_counts[null_counts > 0]
    results.append({
        "name": "No Null Values",
        "passed": len(has_nulls) == 0,
        "detail": has_nulls.to_dict() if len(has_nulls) else "No null values in critical columns"
    })

    # ── Check 4: Age range (21–60) ───────────────────────────────────────────
    age_violations = emp[~emp["age"].between(21, 60)]
    results.append({
        "name": "Age Range (21–60)",
        "passed": len(age_violations) == 0,
        "detail": f"{len(age_violations)} out-of-range records" if len(age_violations) else f"All ages within [21, 60]"
    })

    # ── Check 5: Gender values ───────────────────────────────────────────────
    invalid_genders = emp[~emp["gender"].isin(ALLOWED_GENDERS)]
    results.append({
        "name": "Gender Values",
        "passed": len(invalid_genders) == 0,
        "detail": f"Invalid values: {invalid_genders['gender'].unique().tolist()}" if len(invalid_genders) else f"Allowed set {ALLOWED_GENDERS} respected"
    })

    # ── Check 6: Joining date not in future ──────────────────────────────────
    emp["joining_date"] = pd.to_datetime(emp["joining_date"], errors="coerce")
    future_joins = emp[emp["joining_date"] > pd.Timestamp.today()]
    results.append({
        "name": "Joining Date (No Future)",
        "passed": len(future_joins) == 0,
        "detail": f"{len(future_joins)} future-dated records" if len(future_joins) else "All joining dates are historical"
    })

    # ── Check 7: Status values ───────────────────────────────────────────────
    invalid_status = emp[~emp["status"].isin(ALLOWED_STATUSES)]
    results.append({
        "name": "Employee Status Values",
        "passed": len(invalid_status) == 0,
        "detail": f"Invalid statuses: {invalid_status['status'].unique().tolist()}" if len(invalid_status) else f"All statuses valid"
    })

    return results
