"""
Registration endpoint tests — through the real HTTP layer, hitting the
real database. Confirms: successful registration persists correctly,
password is actually hashed (never stored plain), duplicate email is
rejected with the right status code, and an audit_events row is
written in the same transaction.

Uses httpx.AsyncClient (not FastAPI's sync TestClient) so every test
runs under the same event loop as the rest of the async test suite —
mixing TestClient's own internally-managed loop with directly-async
tests caused "event loop is closed" errors against the shared engine.

These tests commit for real (unlike test_models.py's rollback-based
tests) — that's the point, it's what actually proves get_db()'s
commit-on-success behavior works end-to-end. That means re-running
pytest locally against a persistent DB would hit leftover data from
the previous run, so a fixture cleans up known test rows before each
test in this module runs.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.security import verify_password
from app.db.session import async_session_factory
from app.main import app
from app.models import AuditEvent, User

TEST_EMAILS = ["register-test@example.com", "dup-endpoint-test@example.com"]


@pytest.fixture(autouse=True)
async def _clean_test_users() -> None:
    """Removes this module's known test emails before each test, so
    local re-runs against a persistent DB start from a known state
    instead of colliding with a previous run's leftover rows."""
    async with async_session_factory() as session:
        await session.execute(delete(User).where(User.email.in_(TEST_EMAILS)))
        await session.commit()


async def test_register_creates_user_and_hashes_password() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "register-test@example.com",
                "password": "correct horse battery",
            },
        )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "register-test@example.com"
    assert "password" not in body
    assert "hashed_password" not in body

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "register-test@example.com")
        )
        user = result.scalar_one()
        assert user.hashed_password != "correct horse battery"
        assert verify_password("correct horse battery", user.hashed_password)
        assert not verify_password("wrong password", user.hashed_password)


async def test_duplicate_email_returns_409() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup-endpoint-test@example.com", "password": "whatever123"},
        )
        assert first.status_code == 201

        second = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup-endpoint-test@example.com",
                "password": "different456",
            },
        )
        assert second.status_code == 409


async def test_registration_writes_audit_event() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "register-test@example.com",
                "password": "correct horse battery",
            },
        )

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "register-test@example.com")
        )
        user = result.scalar_one()

        event_result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.entity_id == user.id,
                AuditEvent.action == "user_registered",
            )
        )
        event = event_result.scalar_one()
        assert event.actor_id == user.id
        assert event.event_metadata == {"email": "register-test@example.com"}
