#!/usr/bin/env python3
# src/validators/run_validation.py
"""
PeopleLens Data Validation Framework
=====================================
Orchestrates all individual validators and produces a consolidated
validation report.  Run this after every ETL/generation cycle and
before loading data into PostgreSQL.

Usage:
    python -m src.validators.run_validation
    # or directly:
    python src/validators/run_validation.py
"""

import os
import sys
import json
import datetime
import pandas as pd

# Allow running as a top-level script (python src/validators/run_validation.py)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.validators.validate_employees    import validate_employees
from src.validators.validate_compensation import validate_compensation
from src.validators.validate_performance  import validate_performance
from src.validators.validate_projects     import validate_projects
from src.validators.validate_learning     import validate_learning
from src.validators.validate_exit         import validate_exit

# ──────────────────────────────────────────────────────────────────────────────
# Colour helpers (ANSI – degraded gracefully on Windows)
# ──────────────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

TICK  = "✓"
CROSS = "✗"
WARN  = "⚠"


def _c(text: str, colour: str) -> str:
    """Wrap text in ANSI colour codes."""
    return f"{colour}{text}{RESET}"


# ──────────────────────────────────────────────────────────────────────────────
# Printing helpers
# ──────────────────────────────────────────────────────────────────────────────

WIDTH = 60


def print_header(title: str) -> None:
    print(_c("=" * WIDTH, CYAN))
    print(_c(f"  {title}", BOLD + CYAN))
    print(_c("=" * WIDTH, CYAN))


def print_section(title: str) -> None:
    print(f"\n{_c(BOLD + title, BOLD)}")
    print(_c("-" * WIDTH, CYAN))


def print_result(result: dict) -> None:
    icon   = _c(TICK,  GREEN) if result["passed"] else _c(CROSS, RED)
    name   = result["name"].ljust(38)
    status = _c("PASS", GREEN) if result["passed"] else _c("FAIL", RED)
    detail = result.get("detail", "")
    print(f"  {icon}  {name} [{status}]")
    if not result["passed"] and detail:
        print(f"       {_c(WARN + '  ' + str(detail), YELLOW)}")


def print_summary(all_results: dict[str, list[dict]]) -> None:
    total   = sum(len(v) for v in all_results.values())
    passed  = sum(r["passed"] for v in all_results.values() for r in v)
    failed  = total - passed

    print()
    print(_c("=" * WIDTH, CYAN))
    print(_c(f"  VALIDATION SUMMARY", BOLD + CYAN))
    print(_c("=" * WIDTH, CYAN))
    print(f"  Checks run  : {total}")
    print(f"  {_c('Passed', GREEN)}      : {passed}")
    print(f"  {_c('Failed', RED)}      : {failed}")
    print(_c("-" * WIDTH, CYAN))

    if failed == 0:
        print(_c(f"  {TICK}  ALL CHECKS PASSED — data is safe to load into PostgreSQL", GREEN + BOLD))
    else:
        print(_c(f"  {CROSS}  {failed} CHECK(S) FAILED — fix issues before loading", RED + BOLD))
    print(_c("=" * WIDTH, CYAN))


# ──────────────────────────────────────────────────────────────────────────────
# Optional: write JSON report
# ──────────────────────────────────────────────────────────────────────────────

class _NumpyEncoder(json.JSONEncoder):
    """Serialise numpy / pandas scalar types to plain Python equivalents."""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)


def save_report(all_results: dict[str, list[dict]], report_path: str) -> None:
    """Persist the validation report as JSON for CI/CD pipelines."""
    report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "sections": {}
    }
    for section, results in all_results.items():
        report["sections"][section] = [
            {
                "check": r["name"],
                "passed": bool(r["passed"]),   # ensure plain Python bool
                "detail": str(r.get("detail", ""))
            }
            for r in results
        ]

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, cls=_NumpyEncoder)
    print(f"\n  Report saved → {report_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Main runner
# ──────────────────────────────────────────────────────────────────────────────

def run_validation(save_json: bool = True) -> bool:
    """
    Load all datasets, run all validators, print the report.

    Args:
        save_json: If True, write a JSON report to docs/validation_report.json

    Returns:
        True if all checks passed, False otherwise.
    """
    data_dir = os.path.join(ROOT, "data", "synthetic")

    FILE_MAP = {
        "employees":    "employees.csv",
        "compensation": "compensation.csv",
        "performance":  "performance.csv",
        "projects":     "project_assignments.csv",
        "learning":     "learning.csv",
        "exits":        "exit_records.csv",
    }

    # ── Banner ────────────────────────────────────────────────────────────────
    print_header("PeopleLens  ·  Data Validation Framework")
    print(f"\n  Timestamp : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Data dir  : {data_dir}\n")

    # ── File existence check ──────────────────────────────────────────────────
    print_section("0. File Existence Checks")
    missing = []
    for key, fname in FILE_MAP.items():
        path = os.path.join(data_dir, fname)
        found = os.path.exists(path)
        if not found:
            missing.append(fname)
        icon = _c(TICK, GREEN) if found else _c(CROSS, RED)
        print(f"  {icon}  {fname}")

    if missing:
        print(_c(f"\n  Aborting: {len(missing)} file(s) not found.", RED + BOLD))
        return False

    # ── Load CSVs ─────────────────────────────────────────────────────────────
    print(f"\n  Loading datasets…")
    emp   = pd.read_csv(os.path.join(data_dir, FILE_MAP["employees"]))
    comp  = pd.read_csv(os.path.join(data_dir, FILE_MAP["compensation"]))
    perf  = pd.read_csv(os.path.join(data_dir, FILE_MAP["performance"]))
    proj  = pd.read_csv(os.path.join(data_dir, FILE_MAP["projects"]))
    learn = pd.read_csv(os.path.join(data_dir, FILE_MAP["learning"]))
    exits = pd.read_csv(os.path.join(data_dir, FILE_MAP["exits"]))

    print(f"  {'Dataset':<22} {'Rows':>8}  {'Columns':>8}")
    print(f"  {'-'*42}")
    for label, df in [
        ("Employees",    emp),
        ("Compensation", comp),
        ("Performance",  perf),
        ("Projects",     proj),
        ("Learning",     learn),
        ("Exits",        exits),
    ]:
        print(f"  {label:<22} {len(df):>8,}  {df.shape[1]:>8}")

    # ── Run validators ────────────────────────────────────────────────────────
    all_results: dict[str, list[dict]] = {}

    sections = [
        ("1. Employees",    validate_employees(emp)),
        ("2. Compensation", validate_compensation(comp, emp)),
        ("3. Performance",  validate_performance(perf, emp)),
        ("4. Projects",     validate_projects(proj, emp)),
        ("5. Learning",     validate_learning(learn, emp)),
        ("6. Exit Records", validate_exit(exits, emp)),
    ]

    for title, results in sections:
        print_section(title)
        for r in results:
            print_result(r)
        all_results[title] = results

    # ── Summary ───────────────────────────────────────────────────────────────
    print_summary(all_results)

    # ── JSON report ───────────────────────────────────────────────────────────
    if save_json:
        report_path = os.path.join(ROOT, "docs", "validation_report.json")
        save_report(all_results, report_path)

    all_passed = all(r["passed"] for v in all_results.values() for r in v)
    return all_passed


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    success = run_validation(save_json=True)
    sys.exit(0 if success else 1)
