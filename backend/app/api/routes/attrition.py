"""
backend/app/api/routes/attrition.py
──────────────────────────────────────
Attrition analysis API routes.
Returns aggregated attrition rates — no individual employee data.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

log = logging.getLogger(__name__)
router = APIRouter(prefix="/attrition", tags=["Attrition Analysis"])

VALID_DIMENSIONS = ["department", "location", "level", "gender", "college_tier"]


def _load_employees() -> pd.DataFrame:
    path = ROOT / "data" / "synthetic" / "employees.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Run data_generator/generate_dataset.py first.")
    return pd.read_csv(path, parse_dates=["join_date", "exit_date"])


@router.get("/by-dimension", summary="Attrition Rate by Dimension")
async def get_attrition_by_dimension(
    dimension: str = Query(default="department", description=f"One of: {VALID_DIMENSIONS}")
) -> dict[str, Any]:
    """
    Attrition rate grouped by a demographic dimension.
    Applies k-anonymity (k=10) before returning results.
    """
    if dimension not in VALID_DIMENSIONS:
        raise HTTPException(status_code=400, detail=f"dimension must be one of {VALID_DIMENSIONS}")
    try:
        from analytics.attrition_analysis import compute_attrition_by_dimension
        employees = _load_employees()
        result = compute_attrition_by_dimension(employees, dimension)
        return {"status": "ok", "dimension": dimension, "data": result.to_dict(orient="records")}
    except Exception as e:
        log.error(f"Attrition by dimension error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenure-bands", summary="Attrition Rate by Tenure Band")
async def get_tenure_band_attrition() -> dict[str, Any]:
    """Attrition breakdown by tenure band: <6m, 6-12m, 1-2yr, 2-3yr, 3+yr."""
    try:
        from analytics.attrition_analysis import compute_tenure_attrition_bands
        employees = _load_employees()
        result = compute_tenure_attrition_bands(employees)
        return {"status": "ok", "data": result.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-scores", summary="Attrition Risk Score Distribution")
async def get_risk_score_distribution() -> dict[str, Any]:
    """
    Distribution of attrition risk scores (Low/Medium/High) from ML model.
    Loads pre-computed scores from data/analytics/attrition_scores.csv.
    """
    try:
        scores_path = ROOT / "data" / "analytics" / "attrition_scores.csv"
        if not scores_path.exists():
            return {"status": "no_model", "message": "Run ml/train.py then ml/predict.py to generate risk scores"}

        scores = pd.read_csv(scores_path)
        distribution = scores["risk_tier"].value_counts().to_dict()
        avg_score = float(scores["risk_score"].mean())

        return {
            "status": "ok",
            "distribution": distribution,
            "avg_risk_score": round(avg_score, 4),
            "high_risk_count": int(distribution.get("High", 0)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
