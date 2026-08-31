"""
TrustLake API — Stage 0 placeholder.

This is intentionally minimal: a single route proving the FastAPI service
boots and responds. Real business logic (auth, DB models, profiling, etc.)
starts in Stage 2 per the build roadmap. Do not add routes here beyond
this placeholder without checking which stage they belong to.
"""

from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title="TrustLake API", version="0.0.0")


@app.get("/")
def read_root() -> dict[str, str]:
    """Placeholder route — proves the API container boots and serves requests."""
    return {"message": "Hello, TrustLake"}
