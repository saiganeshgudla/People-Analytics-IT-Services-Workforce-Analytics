"""
backend/app/api/routes/retention.py
──────────────────────────────────────
Retention analysis API routes.
Kaplan-Meier curves and cohort tables — aggregated only.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)
router = APIRouter(prefix="/retention", tags=["Retention Analysis"])


def _load_employees() -> pd.DataFrame:
    path = ROOT / "data" / "synthetic" / "employees.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Run data_generator/generate_dataset.py first.")
    return pd.read_csv(path, parse_dates=["join_date", "exit_date"])


@router.get("/cohort-table", summary="Retention Cohort Table")
async def get_cohort_table() -> dict[str, Any]:
    """
    Retention rates at 6m, 12m, 24m, 36m by college tier and join cohort.
    Cohorts with < 10 members excluded.
    """
    try:
        from analytics.retention_analysis import compute_retention_cohort_table
        employees = _load_employees()
        table = compute_retention_cohort_table(employees)
        return {"status": "ok", "data": table.to_dict(orient="records")}
    except Exception as e:
        log.error(f"Retention cohort error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kaplan-meier", summary="Kaplan-Meier Survival Curves")
async def get_kaplan_meier() -> dict[str, Any]:
    """
    Kaplan-Meier survival curves stratified by college tier.
    Returns timeline points for charting.
    """
    try:
        from analytics.retention_analysis import compute_km_by_college_tier
        employees = _load_employees()
        km_data = compute_km_by_college_tier(employees)
        return {"status": "ok", "data": km_data}
    except ImportError:
        return {
            "status": "lifelines_not_installed",
            "message": "Run: pip install lifelines",
        }
    except Exception as e:
        log.error(f"KM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
