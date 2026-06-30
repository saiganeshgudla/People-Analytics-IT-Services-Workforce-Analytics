"""
data_generator/generate_dataset.py
────────────────────────────────────
PeopleLens — Master Orchestrator

Runs all data generators in order, saves CSVs to data/synthetic/,
and prints a final summary table.

Usage:
    python data_generator/generate_dataset.py
    python data_generator/generate_dataset.py --employees 5000
    python data_generator/generate_dataset.py --seed 99
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

# Add project root to path so relative imports work when called from root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data_generator.employee_generator import generate_employees
from data_generator.salary_generator import generate_salary_history
from data_generator.performance_generator import generate_performance
from data_generator.project_generator import generate_projects
from data_generator.learning_generator import generate_learning
from data_generator.exit_generator import generate_exits
from data_generator.manager_generator import generate_managers


def main(n_employees: int = 12000, seed: int = 42) -> None:
    output_dir = ROOT / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  PeopleLens — Synthetic HR Data Generator")
    print("  NimbusTech · 10,000+ Employees · 5 Years")
    print("=" * 60)

    start = time.time()
    summary = []

    # ── 1. Employees ────────────────────────────────────────────────────────
    print("\n[1/7] Generating employee master...")
    employees = generate_employees(n_total=n_employees, seed=seed)
    path = output_dir / "employees.csv"
    employees.to_csv(path, index=False)
    summary.append(("employees.csv", len(employees), str(path)))

    # ── 2. Salary History ───────────────────────────────────────────────────
    print("\n[2/7] Generating salary history...")
    salary = generate_salary_history(employees, seed=seed)
    path = output_dir / "salary_history.csv"
    salary.to_csv(path, index=False)
    summary.append(("salary_history.csv", len(salary), str(path)))

    # ── 3. Performance Ratings ──────────────────────────────────────────────
    print("\n[3/7] Generating performance ratings...")
    performance = generate_performance(employees, seed=seed)
    path = output_dir / "performance.csv"
    performance.to_csv(path, index=False)
    summary.append(("performance.csv", len(performance), str(path)))

    # ── 4. Project Assignments ──────────────────────────────────────────────
    print("\n[4/7] Generating project assignments...")
    projects = generate_projects(employees, seed=seed)
    path = output_dir / "projects.csv"
    projects.to_csv(path, index=False)
    summary.append(("projects.csv", len(projects), str(path)))

    # ── 5. Learning Records ─────────────────────────────────────────────────
    print("\n[5/7] Generating learning records...")
    learning = generate_learning(employees, seed=seed)
    path = output_dir / "learning.csv"
    learning.to_csv(path, index=False)
    summary.append(("learning.csv", len(learning), str(path)))

    # ── 6. Exit Records ─────────────────────────────────────────────────────
    print("\n[6/7] Generating exit records...")
    exits = generate_exits(employees, seed=seed)
    path = output_dir / "exits.csv"
    exits.to_csv(path, index=False)
    summary.append(("exits.csv", len(exits), str(path)))

    # ── 7. Manager Hierarchy ────────────────────────────────────────────────
    print("\n[7/7] Generating manager hierarchy...")
    managers = generate_managers(employees, seed=seed)
    path = output_dir / "managers.csv"
    managers.to_csv(path, index=False)
    summary.append(("managers.csv", len(managers), str(path)))

    elapsed = time.time() - start

    # ── Final Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  ✅ Dataset generation complete! ({elapsed:.1f}s)")
    print("=" * 60)
    print(f"\n{'File':<25} {'Rows':>10}  {'Path'}")
    print("-" * 70)
    for fname, rows, fpath in summary:
        print(f"{fname:<25} {rows:>10,}  {fpath}")
    print("-" * 70)
    total_rows = sum(r for _, r, _ in summary)
    print(f"{'TOTAL':<25} {total_rows:>10,}")
    print(f"\n📁 Files saved to: {output_dir}\n")

    # Quick data quality check
    print("── Data Quality Check ──────────────────────────────────────")
    active_count = employees["is_active"].sum()
    exited_count = (~employees["is_active"]).sum()
    attrition_rate = exited_count / len(employees)
    print(f"  Headcount   : {len(employees):,}")
    print(f"  Active       : {active_count:,}")
    print(f"  Exited       : {exited_count:,}")
    print(f"  Attrition %  : {attrition_rate:.1%}")
    print(f"  Avg salary   : ₹{salary.groupby('employee_id')['base_salary'].last().mean():,.0f}")
    print(f"  Avg rating   : {performance['rating'].mean():.2f}")
    female_pct = (employees["gender"] == "Female").mean()
    print(f"  Female %     : {female_pct:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic HR data for PeopleLens.")
    parser.add_argument("--employees", type=int, default=12000, help="Number of employees to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    main(n_employees=args.employees, seed=args.seed)
