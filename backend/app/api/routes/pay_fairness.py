"""
backend/app/api/routes/pay_fairness.py
────────────────────────────────────────
Pay fairness analysis API routes.
Returns gender pay gap metrics by bucket — no individual salary data.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)
router = APIRouter(prefix="/pay-fairness", tags=["Pay Fairness"])


def _load_data():
    emp_path = ROOT / "data" / "synthetic" / "employees.csv"
    sal_path = ROOT / "data" / "synthetic" / "salary_history.csv"
    if not emp_path.exists() or not sal_path.exists():
        raise HTTPException(status_code=503, detail="Run data_generator/generate_dataset.py first.")
    employees = pd.read_csv(emp_path)
    salary = pd.read_csv(sal_path, parse_dates=["effective_date"])
    return employees, salary


@router.get("/gender-gap", summary="Gender Pay Gap Analysis")
async def get_gender_pay_gap(
    group_by: str = Query(default="level", description="Grouping: level, department, location"),
    flagged_only: bool = Query(default=False),
) -> dict[str, Any]:
    """
    Gender pay ratio within each bucket. Flags buckets outside ±5%.
    Buckets with < 10 employees per gender excluded (k-anonymity).
    """
    try:
        from analytics.pay_fairness import compute_comp_ratios, compute_pay_fairness_by_gender
        employees, salary = _load_data()
        comp = compute_comp_ratios(salary, employees)

        group_cols = [group_by] if group_by in ["level", "department", "location"] else ["level"]
        result = compute_pay_fairness_by_gender(comp, group_cols=group_cols)

        if flagged_only and not result.empty:
            result = result[result["disparity_flag"] == True]

        return {
            "status": "ok",
            "flagged_buckets": int(result["disparity_flag"].sum()) if not result.empty else 0,
            "data": result.to_dict(orient="records"),
        }
    except Exception as e:
        log.error(f"Pay fairness error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall", summary="Overall Pay Fairness KPIs")
async def get_overall_pay_fairness() -> dict[str, Any]:
    """Headline pay fairness metrics: overall gender pay ratio, pay gap %."""
    try:
        from analytics.pay_fairness import compute_comp_ratios, compute_overall_pay_fairness
        employees, salary = _load_data()
        comp = compute_comp_ratios(salary, employees)
        result = compute_overall_pay_fairness(comp)
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
