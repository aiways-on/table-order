"""Health + metrics endpoints.  [RES-06][NFR-O3]

- /health       shallow liveness (no dependencies)
- /health/deep  readiness incl. DB connectivity check
- /metrics      in-process metrics snapshot
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.logging import get_logger
from app.core.metrics import metrics

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Shallow liveness — fast, no dependency calls."""
    return {"status": "ok"}


@router.get("/health/deep")
async def health_deep() -> JSONResponse:
    """Deep readiness — verifies DB connectivity; 503 if unavailable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    except Exception:
        logger.error("health_deep_db_unavailable")
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "unavailable"})


@router.get("/metrics")
async def get_metrics() -> dict:
    return metrics.snapshot()
