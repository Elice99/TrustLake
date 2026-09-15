"""
TrustLake API.

Real routes start landing here from Stage 2 Day 4 onward (auth first).
The root "/" route remains as a basic liveness check; a proper
DB-aware /health endpoint is a later Stage 2 item, not built yet.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes.auth import router as auth_router
from app.core.config import settings

logger = logging.getLogger("trustlake.api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Confirms required env vars loaded successfully (fail-fast already
    happened at import time in app.core.config — this just makes that
    visible in the logs, and gives `settings` a real use)."""
    logger.info("Config loaded. Target database: %s", settings.postgres_db)
    yield


app = FastAPI(title="TrustLake API", version="0.0.0", lifespan=lifespan)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    """Placeholder route — proves the API container boots and serves requests."""
    return {"message": "Hello, TrustLake"}
