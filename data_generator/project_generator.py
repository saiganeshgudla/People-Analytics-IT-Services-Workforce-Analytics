"""
data_generator/project_generator.py
─────────────────────────────────────
Generates project assignment records for NimbusTech employees.
- 200 projects across 5 years
- Employees can work on 1-4 projects simultaneously
- Project types: Product, Services, Consulting, R&D, Internal
- Client industries: BFSI, Healthcare, Retail, Manufacturing, Telecom
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta

PROJECT_TYPES = ["Product Development", "Managed Services", "Consulting", "R&D", "Digital Transformation", "Internal"]
CLIENT_INDUSTRIES = ["BFSI", "Healthcare", "Retail & E-Commerce", "Manufacturing", "Telecom", "Logistics", "Energy", "Government"]
CLIENT_WEIGHTS = [0.30, 0.15, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]
ROLES_IN_PROJECT = ["Developer", "Senior Developer", "Tech Lead", "QA Engineer", "DevOps", "Analyst", "Architect", "Manager", "Consultant"]


def generate_projects(employees: pd.DataFrame, n_projects: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generate project assignment records.

    Args:
        employees: Output of employee_generator.generate_employees()
        n_projects: Number of distinct projects.
        seed: Random seed.

    Returns:
        DataFrame with (employee_id, project_id, project_name, ..., start_date, end_date)
    """
    rng = np.random.default_rng(seed)

    # Generate project master data
    projects = []
    for i in range(1, n_projects + 1):
        proj_start = date(2019, 1, 1) + timedelta(days=int(rng.integers(0, 365 * 4)))
        duration_months = int(rng.integers(6, 36))
        proj_end = proj_start + timedelta(days=duration_months * 30)
        proj_end = min(proj_end, date(2024, 12, 31))

        projects.append({
            "project_id": f"PRJ_{i:04d}",
            "project_name": f"Project_{i:04d}",
            "project_type": rng.choice(PROJECT_TYPES),
            "client_industry": rng.choice(CLIENT_INDUSTRIES, p=CLIENT_WEIGHTS),
            "proj_start": proj_start,
            "proj_end": proj_end,
        })

    proj_df = pd.DataFrame(projects)

    # Assign employees to projects
    records = []
    for _, emp in employees.iterrows():
        emp_id = emp["employee_id"]
        join_date = pd.Timestamp(emp["join_date"]).date()
        exit_date = pd.Timestamp(emp["exit_date"]).date() if pd.notna(emp["exit_date"]) else date(2024, 12, 31)

        # Filter projects that overlap with employee tenure
        valid_projects = proj_df[
            (proj_df["proj_start"] < exit_date) &
            (proj_df["proj_end"] > join_date)
        ]

        if valid_projects.empty:
            continue

        n_assignments = int(rng.integers(1, min(5, len(valid_projects) + 1)))
        assigned = valid_projects.sample(n=n_assignments, random_state=int(rng.integers(0, 99999)))

        for _, proj in assigned.iterrows():
            # Employee's start/end on this project (constrained by tenure)
            actual_start = max(join_date, proj["proj_start"])
            actual_end = min(exit_date, proj["proj_end"])

            if actual_start >= actual_end:
                continue

            records.append({
                "employee_id": emp_id,
                "project_id": proj["project_id"],
                "project_name": proj["project_name"],
                "project_type": proj["project_type"],
                "client_industry": proj["client_industry"],
                "start_date": actual_start,
                "end_date": actual_end,
                "role_in_project": rng.choice(ROLES_IN_PROJECT),
            })

    df = pd.DataFrame(records)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    print(f"✅ Generated {len(df):,} project assignments across {n_projects} projects")
    return df


if __name__ == "__main__":
    from employee_generator import generate_employees
    emps = generate_employees()
    proj = generate_projects(emps)
    print(proj["client_industry"].value_counts())
