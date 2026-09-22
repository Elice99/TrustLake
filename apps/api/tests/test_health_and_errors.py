"""
Tests for /health and the consistent error envelope.

The DB-down case for /health is simulated via FastAPI's own
dependency_overrides mechanism (substituting a broken get_db that
always raises) rather than actually stopping the real Postgres
container mid-test-suite, which would break every other test running
against the same database.
"""

from collections.abc import AsyncGenerator

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app


async def test_health_returns_ok_when_db_is_reachable() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_health_returns_503_with_envelope_when_db_is_unreachable() -> None:
    class _BrokenSession:
        """Mimics a session that connects fine but fails on the actual
        query — the realistic shape of a real Postgres outage. A
        dependency that raises immediately on injection (before the
        route body even runs) would test a different, less realistic
        failure point than what app.main.health_check's try/except is
        actually built to catch."""

        async def execute(self, *_args: object, **_kwargs: object) -> None:
            raise ConnectionError("simulated: database is unreachable")

    async def _broken_get_db() -> AsyncGenerator[AsyncSession]:
        yield _BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
    finally:
        # Always remove the override, even if the assertion below fails —
        # otherwise every test after this one would hit the broken DB too.
        del app.dependency_overrides[get_db]

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "service_unavailable"
    assert body["error"]["message"] == "Database is unreachable"


async def test_validation_error_uses_the_same_envelope_shape() -> None:
    """A malformed request body (invalid email format) triggers
    Pydantic's validation, not our own route code — confirms that path
    also lands in the same {"error": {...}} shape, not FastAPI's
    different default shape for validation errors."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-a-valid-email", "password": "whatever123"},
        )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list)


async def test_missing_route_returns_envelope_shaped_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
