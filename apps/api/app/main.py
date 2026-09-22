"""
TrustLake API.

Real routes start landing here from Stage 2 Day 4 onward (auth first).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.auth import router as auth_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.db.session import get_db

logger = logging.getLogger("trustlake.api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Confirms required env vars loaded successfully (fail-fast already
    happened at import time in app.core.config — this just makes that
    visible in the logs, and gives `settings` a real use)."""
    logger.info("Config loaded. Target database: %s", settings.postgres_db)
    yield


app = FastAPI(title="TrustLake API", version="0.0.0", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    """Placeholder route — proves the API container boots and serves requests."""
    return {"message": "Hello, TrustLake"}


@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),  # noqa: B008 — FastAPI's DI pattern
) -> dict[str, str]:
    """Real connectivity check, not just "the process is alive" — per
    the architecture doc's requirement. Runs an actual query; if
    Postgres is unreachable, this raises, and the exception handler in
    app.core.exception_handlers turns it into a proper 503 with the
    standard error envelope — deliberately not swallowed into a
    generic 200 or an unstructured crash."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unreachable",
        ) from exc

    return {"status": "ok", "database": "connected"}
