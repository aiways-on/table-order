"""FastAPI application factory for the table-order backend (modular monolith).

Wires cross-cutting infrastructure from U1 backend-core. Domain routers
(auth/menu/order) are registered here as later units are built.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio

from app.auth.router import router as auth_router
from app.menu.router import router as menu_router
from app.order.router import router as order_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.events import event_bus
from app.core.health import router as health_router
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # SSE fan-out: let sync endpoints publish onto subscriber queues safely. [NFR-P2]
    event_bus.attach_loop(asyncio.get_running_loop())
    logger.info("app_startup", env=get_settings().app_env)
    yield
    # Graceful shutdown: uvicorn drains in-flight requests / SSE. [RES-07]
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Table-Order API", version="0.1.0", lifespan=lifespan)

    # CORS: explicit origins only, no wildcard. [SEC-08]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Middleware ordering (added last = outermost): correlation id wraps everything.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(menu_router)
    app.include_router(order_router)

    return app


app = create_app()
