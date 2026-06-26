"""FastAPI application entrypoint.

Run (from the ``backend`` directory)::

    uvicorn app.main:app --reload

Interactive API docs are served at ``/docs`` (Swagger) and ``/redoc``.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import get_logger, setup_logging
from app.database import async_engine

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks: verify DB connectivity, dispose the engine cleanly."""
    logger.info("Starting %s v%s (env=%s).", settings.PROJECT_NAME, __version__, settings.ENV)
    if async_engine is not None:
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connectivity verified.")
        except Exception:  # noqa: BLE001 — log and continue; /health reflects real state
            logger.exception("Database connectivity check failed at startup.")
    else:
        logger.error("Async database engine is not configured; check .env settings.")
    yield
    if async_engine is not None:
        await async_engine.dispose()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "REST API for digitizing Cooperative Society bye-law documents: upload, "
        "automated clause extraction, review, versioning, search and export."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — allow the browser frontend to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"], summary="Liveness & DB readiness probe")
async def health_check() -> dict:
    """Report application and database health for monitoring/deployment probes."""
    db_status = "unknown"
    if async_engine is None:
        db_status = "not_configured"
    else:
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:  # noqa: BLE001
            db_status = "unavailable"
    overall = "ok" if db_status == "connected" else "degraded"
    return {
        "status": overall,
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "environment": settings.ENV,
        "database": db_status,
    }


@app.get("/", tags=["System"], summary="API root")
async def root() -> dict:
    return {
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
