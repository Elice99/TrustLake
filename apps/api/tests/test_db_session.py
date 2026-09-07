"""
Tests for the async database session management.

These require a real Postgres reachable at DATABASE_URL — they are
integration tests, not unit tests with a mocked connection, matching
the roadmap's explicit requirement (Stage 2 build step 9): "using a
real (test) database, not mocks for the DB layer."
"""

from sqlalchemy import text

from app.db.session import get_db


async def test_get_db_yields_working_session() -> None:
    async for session in get_db():
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
