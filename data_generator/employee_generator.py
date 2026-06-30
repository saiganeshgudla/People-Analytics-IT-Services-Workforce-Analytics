"""
data_generator/employee_generator.py
─────────────────────────────────────
Generates synthetic employee master records for NimbusTech.
- 10,000+ employees over 5 years
- Realistic tenure/attrition distributions matching 18% voluntary attrition
- No PII: employee_id only (no names, emails)
- Gender representation: ~40% female, ~60% male (IT sector realistic)
- College tier distribution: 15% T1 (IIT/NIT), 45% T2, 40% T3
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────
DEPARTMENTS = ["Engineering", "Analytics", "QA", "Operations", "DevOps", "Cloud", "Security", "Consulting"]
ROLES_BY_DEPT: dict[str, list[str]] = {
    "Engineering":  ["Software Engineer", "Senior Software Engineer", "Tech Lead", "Principal Engineer", "Architect"],
    "Analytics":    ["Data Analyst", "Senior Data Analyst", "Analytics Lead", "Data Scientist", "Analytics Manager"],
    "QA":           ["QA Engineer", "Senior QA Engineer", "QA Lead", "Test Architect"],
    "Operations":   ["Operations Analyst", "Operations Lead", "Delivery Manager"],
    "DevOps":       ["DevOps Engineer", "Senior DevOps", "Site Reliability Engineer", "Platform Engineer"],
    "Cloud":        ["Cloud Engineer", "Cloud Architect", "Cloud Consultant"],
    "Security":     ["Security Analyst", "Security Engineer", "InfoSec Lead"],
    "Consulting":   ["Associate Consultant", "Consultant", "Senior Consultant", "Principal Consultant"],
}
LEVELS = {
    "Junior":     ["L1", "L2"],
    "Mid":        ["L3", "L4"],
    "Senior":     ["L5", "L6"],
    "Leadership": ["L7", "L8"],
}
LEVEL_FLAT = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"]
LOCATIONS = ["Bengaluru", "Hyderabad", "Chennai", "Pune", "Mumbai", "Delhi NCR", "Kolkata", "Ahmedabad", "Kochi", "Bhubaneswar"]
LOCATION_WEIGHTS = [0.28, 0.20, 0.15, 0.12, 0.08, 0.07, 0.04, 0.03, 0.02, 0.01]
EXIT_REASONS = ["Better Opportunity", "Higher Pay", "Work-Life Balance", "Relocation", "Personal Reasons", "Career Change", "Manager Issues"]
EXIT_REASON_WEIGHTS = [0.35, 0.25, 0.15, 0.10, 0.08, 0.05, 0.02]
COLLEGE_TIERS = [1, 2, 3]
COLLEGE_TIER_WEIGHTS = [0.15, 0.45, 0.40]


def _random_date(start: date, end: date, rng: np.random.Generator) -> date:
    delta = (end - start).days
    return start + timedelta(days=int(rng.integers(0, delta)))


def _assign_level(dept: str, rng: np.random.Generator) -> str:
    """Realistic level distribution — bell curve around L3/L4."""
    weights = [0.10, 0.18, 0.28, 0.22, 0.12, 0.06, 0.03, 0.01]
    return rng.choice(LEVEL_FLAT, p=weights)


def _assign_role(dept: str, level: str, rng: np.random.Generator) -> str:
    roles = ROLES_BY_DEPT[dept]
    level_num = int(level[1])
    # Higher levels → senior roles (last in list)
    idx = min(int((level_num / 8) * len(roles)), len(roles) - 1)
    # Add some noise
    idx = max(0, min(len(roles) - 1, idx + rng.integers(-1, 2)))
    return roles[idx]


def generate_employees(n_total: int = 12000, seed: int = 42) -> pd.DataFrame:
    """
    Generate employee master records.

    Args:
        n_total: Target number of employee records (active + exited).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with one row per employee.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    start_date = date(2019, 1, 1)
    end_date = date(2024, 12, 31)
    today = date(2024, 12, 31)

    records = []
    manager_pool: list[str] = []  # managers are employees at L5+

    for i in range(1, n_total + 1):
        emp_id = f"EMP_{i:05d}"
        dept = rng.choice(DEPARTMENTS)
        level = _assign_level(dept, rng)
        role = _assign_role(dept, level, rng)
        gender = rng.choice(["Male", "Female"], p=[0.60, 0.40])
        location = rng.choice(LOCATIONS, p=LOCATION_WEIGHTS)
        college_tier = rng.choice(COLLEGE_TIERS, p=COLLEGE_TIER_WEIGHTS)
        birth_year = int(rng.integers(1985, 2001))

        # Join date: distributed across 5 years with growth (more recent = more joiners)
        join_weights = [0.10, 0.15, 0.18, 0.25, 0.32]  # 2019→2023
        join_year = rng.choice([2019, 2020, 2021, 2022, 2023], p=join_weights)
        join_start = date(join_year, 1, 1)
        join_end = date(join_year, 12, 31)
        join_date = _random_date(join_start, join_end, rng)

        # Attrition simulation
        # Base 18% annual rate; higher for T3 college, lower level, manager issues
        base_attrition_rate = 0.18
        tier_modifier = {1: -0.04, 2: 0.0, 3: 0.06}[college_tier]
        level_modifier = {"L1": 0.08, "L2": 0.05, "L3": 0.02, "L4": 0.0, "L5": -0.03, "L6": -0.05, "L7": -0.07, "L8": -0.09}[level]
        annual_attrition = min(0.55, max(0.02, base_attrition_rate + tier_modifier + level_modifier))

        # Did this person leave?
        tenure_years_possible = (today - join_date).days / 365.25
        p_left = 1 - (1 - annual_attrition) ** tenure_years_possible

        is_active = rng.random() > p_left
        exit_date: Optional[date] = None
        exit_reason: Optional[str] = None

        if not is_active:
            # Exit between 3 months and their tenure
            min_tenure_days = 90
            max_tenure_days = (today - join_date).days - 30
            if max_tenure_days > min_tenure_days:
                tenure_days = int(rng.integers(min_tenure_days, max_tenure_days))
                exit_date = join_date + timedelta(days=tenure_days)
                exit_reason = rng.choice(EXIT_REASONS, p=EXIT_REASON_WEIGHTS)
            else:
                is_active = True  # edge case: too new

        # Manager assignment (senior employees become managers)
        manager_id: Optional[str] = None
        if level in ["L5", "L6", "L7", "L8"] and not manager_pool:
            manager_pool.append(emp_id)
        elif manager_pool:
            manager_id = rng.choice(manager_pool)

        if level in ["L5", "L6", "L7", "L8"] and emp_id not in manager_pool:
            manager_pool.append(emp_id)

        records.append({
            "employee_id": emp_id,
            "join_date": join_date,
            "birth_year": birth_year,
            "gender": gender,
            "department": dept,
            "role": role,
            "level": level,
            "location": location,
            "college_tier": college_tier,
            "is_active": is_active,
            "exit_date": exit_date,
            "exit_reason": exit_reason,
            "manager_id": manager_id,
        })

    df = pd.DataFrame(records)
    df["join_date"] = pd.to_datetime(df["join_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    # Stats summary
    total = len(df)
    exited = df["is_active"].eq(False).sum()
    print(f"✅ Generated {total:,} employees | Active: {total-exited:,} | Exited: {exited:,} | Attrition: {exited/total:.1%}")
    print(f"   Gender split: Male={df['gender'].eq('Male').mean():.1%} Female={df['gender'].eq('Female').mean():.1%}")
    print(f"   College tiers: T1={df['college_tier'].eq(1).mean():.1%} T2={df['college_tier'].eq(2).mean():.1%} T3={df['college_tier'].eq(3).mean():.1%}")

    return df


if __name__ == "__main__":
    df = generate_employees()
    print(df.head())
    print(df.dtypes)
