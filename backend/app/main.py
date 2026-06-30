"""
backend/app/main.py
────────────────────
PeopleLens FastAPI application entry point.

Features:
- CORS for Streamlit dashboard
- Automatic Swagger UI at /docs
- Health check at /health
- Versioned API under /api/v1/
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.core.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    log.info(f"🚀 PeopleLens API starting — env={settings.env}")
    yield
    log.info("PeopleLens API shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## PeopleLens Workforce Analytics API

Built for **NimbusTech** People Analytics team.

### Features
- 🔍 Attrition risk analysis (XGBoost + SHAP)
- 👔 Manager-effect analysis with peer benchmarking
- ⚖️ Pay fairness audit (gender pay gap with statistical tests)
- 📈 Retention curves (Kaplan-Meier by college tier)
- 🎯 Executive KPI summary

### Privacy
All endpoints return **aggregated data only** with k-anonymity (k≥10).
No individual employee records are exposed.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/health", tags=["System"], summary="Health Check")
async def health_check() -> dict:
    """Returns API health status. Used by Docker healthcheck."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.env,
    }


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "message": "Welcome to PeopleLens API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
