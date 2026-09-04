"""
TrustLake API — Stage 0 placeholder.

This is intentionally minimal: a single route proving the FastAPI service
boots and responds. Real business logic (auth, DB models, profiling, etc.)
starts in Stage 2 per the build roadmap. Do not add routes here beyond
this placeholder without checking which stage they belong to.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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


@app.get("/")
def read_root() -> dict[str, str]:
    """Placeholder route — proves the API container boots and serves requests."""
    return {"message": "Hello, TrustLake"}
