"""
Async database engine and session management.

One engine per process, created once at import time. Sessions are
created per-request via get_db(), a FastAPI dependency — never share a
session across requests or hold one open longer than a request's
lifetime.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    # echo=True is useful for local debugging (logs every SQL statement)
    # but noisy and not something to leave on by default. Flip manually
    # when actively debugging a query, not via an env var yet — that's
    # more configuration surface than Stage 2 needs.
    echo=False,
    pool_pre_ping=True,  # Detects and recycles dead connections, e.g.
    # after Postgres restarts mid-session — avoids a confusing "server
    # closed the connection unexpectedly" error on the next query.
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency — yields a session scoped to a single request.
    The session is always closed after the request, even if an
    exception is raised partway through a route handler."""
    async with async_session_factory() as session:
        yield session
