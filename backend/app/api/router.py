"""
backend/app/api/router.py
──────────────────────────
Aggregates all API routers into a single APIRouter.
"""

from fastapi import APIRouter

from backend.app.api.routes.executive import router as executive_router
from backend.app.api.routes.attrition import router as attrition_router
from backend.app.api.routes.manager_effect import router as manager_router
from backend.app.api.routes.pay_fairness import router as pay_fairness_router
from backend.app.api.routes.retention import router as retention_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(executive_router)
api_router.include_router(attrition_router)
api_router.include_router(manager_router)
api_router.include_router(pay_fairness_router)
api_router.include_router(retention_router)
