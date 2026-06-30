"""
backend/app/api/routes/manager_effect.py
──────────────────────────────────────────
Manager-effect analysis API routes.
Returns manager team attrition vs peers — no individual employee data.
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
router = APIRouter(prefix="/manager-effect", tags=["Manager Effect"])


def _load_data():
    emp_path = ROOT / "data" / "synthetic" / "employees.csv"
    mgr_path = ROOT / "data" / "synthetic" / "managers.csv"
    if not emp_path.exists():
        raise HTTPException(status_code=503, detail="Run data_generator/generate_dataset.py first.")
    employees = pd.read_csv(emp_path, parse_dates=["join_date", "exit_date"])
    managers = pd.read_csv(mgr_path) if mgr_path.exists() else pd.DataFrame()
    return employees, managers


@router.get("/rankings", summary="Manager Attrition Rankings")
async def get_manager_rankings(
    top_n: int = Query(default=20, ge=5, le=100),
    department: str = Query(default=None),
    flag_only: bool = Query(default=False, description="Return only flagged (high-risk) managers"),
) -> dict[str, Any]:
    """
    Manager team attrition rates, benchmarked against peers.
    Only managers with team_size >= 5 are shown (k-anonymity).
    """
    try:
        from analytics.manager_effect import compute_manager_attrition
        employees, managers = _load_data()
        result = compute_manager_attrition(employees, managers)

        if department:
            result = result[result["department"] == department]
        if flag_only:
            result = result[result["risk_flag"] == True]

        result = result.head(top_n)
        return {
            "status": "ok",
            "total_managers": len(result),
            "flagged_managers": int(result["risk_flag"].sum()),
            "data": result.to_dict(orient="records"),
        }
    except Exception as e:
        log.error(f"Manager effect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark", summary="Peer Benchmark Summary")
async def get_peer_benchmark() -> dict[str, Any]:
    """Summary of peer-benchmarked attrition by (level, department)."""
    try:
        from analytics.manager_effect import compute_manager_attrition
        employees, managers = _load_data()
        result = compute_manager_attrition(employees, managers)

        if result.empty:
            return {"status": "ok", "data": []}

        peer_cols = ["level", "department"] if "level" in result.columns else ["department"]
        benchmark = result.groupby(peer_cols).agg(
            n_managers=("manager_id", "count"),
            avg_attrition=("attrition_rate", "mean"),
            flagged_count=("risk_flag", "sum"),
        ).reset_index()

        return {"status": "ok", "data": benchmark.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
