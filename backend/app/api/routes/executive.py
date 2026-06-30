"""
backend/app/api/routes/executive.py
─────────────────────────────────────
Executive dashboard API: headline KPIs, 3 charts, yearly trend.
Returns ONLY aggregated data — no row-level employee data.
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
router = APIRouter(prefix="/executive", tags=["Executive Dashboard"])


def _load_employees() -> pd.DataFrame:
    path = ROOT / "data" / "synthetic" / "employees.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Synthetic data not found. Run generate_dataset.py first.")
    return pd.read_csv(path, parse_dates=["join_date", "exit_date"])


@router.get("/kpis", summary="Executive KPI Summary")
async def get_executive_kpis() -> dict[str, Any]:
    """
    Returns headline KPIs for the CHRO executive briefing:
    - Total headcount, active employees, attrition rate
    - Median salary, avg performance rating
    - Gender diversity %, Year-1 attrition rate
    """
    try:
        from analytics.executive_kpis import compute_executive_summary
        employees = _load_employees()

        sal_path = ROOT / "data" / "synthetic" / "salary_history.csv"
        salary = pd.read_csv(sal_path, parse_dates=["effective_date"]) if sal_path.exists() else None

        perf_path = ROOT / "data" / "synthetic" / "performance.csv"
        performance = pd.read_csv(perf_path) if perf_path.exists() else None

        kpis = compute_executive_summary(employees, salary, performance)
        return {"status": "ok", "data": kpis}
    except Exception as e:
        log.error(f"Executive KPIs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend", summary="Yearly Attrition Trend")
async def get_attrition_trend() -> dict[str, Any]:
    """Year-over-year headcount and attrition rate (2019–2024)."""
    try:
        from analytics.executive_kpis import compute_yearly_attrition_trend
        employees = _load_employees()
        trend = compute_yearly_attrition_trend(employees)
        return {"status": "ok", "data": trend.to_dict(orient="records")}
    except Exception as e:
        log.error(f"Attrition trend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
