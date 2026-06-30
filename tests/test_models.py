"""
tests/test_models.py
─────────────────────
Unit tests for analytics and ML modules.
Tests the core analytical logic without requiring a database connection.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ── Analytics Statistics Tests ─────────────────────────────────────────────────

def test_bootstrap_ci_returns_tuple():
    from analytics.statistics import bootstrap_ci
    data = np.random.normal(100, 10, 100)
    lo, hi = bootstrap_ci(data, n_bootstrap=100)
    assert isinstance(lo, float)
    assert isinstance(hi, float)
    assert lo < hi


def test_bootstrap_ci_single_element():
    from analytics.statistics import bootstrap_ci
    lo, hi = bootstrap_ci([42.0], n_bootstrap=100)
    assert np.isnan(lo)


def test_proportion_ci_valid():
    from analytics.statistics import proportion_ci
    lo, hi = proportion_ci(successes=10, n=100)
    assert 0.0 <= lo <= hi <= 1.0


def test_proportion_ci_zero_n():
    from analytics.statistics import proportion_ci
    lo, hi = proportion_ci(0, 0)
    assert lo == 0.0 and hi == 0.0


def test_k_anonymity_guard_filters_small_groups():
    from analytics.statistics import k_anonymity_guard
    df = pd.DataFrame({"group": ["A", "A", "B"], "headcount": [15, 15, 5]})
    result = k_anonymity_guard(df, ["group"], k=10)
    assert all(result["headcount"] >= 10)


def test_welch_t_test_significant():
    from analytics.statistics import welch_t_test
    group_a = np.random.normal(100, 10, 50)
    group_b = np.random.normal(150, 10, 50)
    t_stat, p_value = welch_t_test(group_a, group_b)
    assert p_value < 0.01  # very different groups → significant


# ── Data Generator Tests ─────────────────────────────────────────────────────

def test_employee_generator_count():
    from data_generator.employee_generator import generate_employees
    df = generate_employees(n_total=100, seed=99)
    assert len(df) == 100


def test_employee_generator_no_pii():
    from data_generator.employee_generator import generate_employees
    df = generate_employees(n_total=50, seed=99)
    # No columns that could contain names, emails, phones
    pii_columns = ["name", "first_name", "last_name", "email", "phone", "address"]
    for col in pii_columns:
        assert col not in df.columns, f"PII column '{col}' found!"


def test_employee_generator_has_required_columns():
    from data_generator.employee_generator import generate_employees
    df = generate_employees(n_total=50, seed=99)
    required = ["employee_id", "join_date", "gender", "department", "level", "location", "college_tier"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_employee_generator_attrition_realistic():
    """Attrition rate should be in a realistic range (10–30%)."""
    from data_generator.employee_generator import generate_employees
    df = generate_employees(n_total=1000, seed=42)
    attrition_rate = (~df["is_active"]).mean()
    assert 0.10 <= attrition_rate <= 0.35, f"Attrition rate out of range: {attrition_rate:.1%}"


def test_salary_generator_positive_salaries():
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    emps = generate_employees(n_total=100, seed=42)
    sal = generate_salary_history(emps, seed=42)
    assert (sal["base_salary"] > 0).all()
    assert len(sal) >= len(emps)  # at least one record per employee


def test_performance_ratings_in_range():
    from data_generator.employee_generator import generate_employees
    from data_generator.performance_generator import generate_performance
    emps = generate_employees(n_total=100, seed=42)
    perf = generate_performance(emps, seed=42)
    assert perf["rating"].between(1.0, 5.0).all()


# ── Analytics Tests ────────────────────────────────────────────────────────────

def test_attrition_by_dimension_returns_df():
    from data_generator.employee_generator import generate_employees
    from analytics.attrition_analysis import compute_attrition_by_dimension
    emps = generate_employees(n_total=500, seed=42)
    result = compute_attrition_by_dimension(emps, "department", k=5)
    assert isinstance(result, pd.DataFrame)
    assert "attrition_rate" in result.columns
    assert (result["attrition_rate"] >= 0).all()
    assert (result["attrition_rate"] <= 1).all()


def test_overall_kpis_structure():
    from data_generator.employee_generator import generate_employees
    from analytics.attrition_analysis import compute_overall_attrition_kpis
    emps = generate_employees(n_total=500, seed=42)
    kpis = compute_overall_attrition_kpis(emps)
    required_keys = ["total_headcount", "active_employees", "exited_employees", "overall_attrition_rate"]
    for key in required_keys:
        assert key in kpis, f"Missing KPI: {key}"


def test_pay_fairness_returns_flagged_column():
    from data_generator.employee_generator import generate_employees
    from data_generator.salary_generator import generate_salary_history
    from analytics.pay_fairness import compute_comp_ratios, compute_pay_fairness_by_gender
    emps = generate_employees(n_total=1000, seed=42)
    sal = generate_salary_history(emps, seed=42)
    sal["effective_date"] = pd.to_datetime(sal["effective_date"])
    comp = compute_comp_ratios(sal, emps)
    result = compute_pay_fairness_by_gender(comp, group_cols=["level"], k=5)
    if not result.empty:
        assert "disparity_flag" in result.columns
        assert result["disparity_flag"].dtype == bool
