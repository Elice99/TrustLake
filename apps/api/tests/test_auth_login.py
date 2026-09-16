"""
Login, /me, and JWT expiration tests. Registration is covered in
test_auth.py — this file covers everything added in Day 5.

The expired-token test builds a token with an already-past expiration
directly (not by waiting 30 real minutes for one to actually expire) —
same real verification code path (decode_access_token), just without
burning half an hour per test run.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import async_session_factory
from app.main import app
from app.models import User

TEST_EMAIL = "login-day5-test@example.com"
TEST_PASSWORD = "correct horse battery staple"


@pytest.fixture(autouse=True)
async def _clean_test_user() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(User).where(User.email == TEST_EMAIL))
        await session.commit()


async def _register() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )


async def test_login_returns_valid_token_and_me_works() -> None:
    await _register()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert login_response.json()["token_type"] == "bearer"

        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == TEST_EMAIL


async def test_login_wrong_password_returns_401() -> None:
    await _register()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": TEST_EMAIL, "password": "wrong password entirely"},
        )
        assert response.status_code == 401


async def test_login_nonexistent_email_returns_same_401_as_wrong_password() -> None:
    """The status code and message must be identical to the wrong-
    password case — see app/services/auth.py's authenticate_user
    docstring for why (prevents user enumeration)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody-registered@example.com", "password": "whatever"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"


async def test_me_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


async def test_me_with_garbage_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401


async def test_expired_token_is_rejected() -> None:
    """Builds a token with an expiration in the past, bypassing
    create_access_token's real 30-minute default — proves the actual
    expiration check works without waiting for real time to pass."""
    already_expired = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(already_expired)


async def test_token_for_deleted_user_is_rejected_at_the_route_level() -> None:
    """decode_access_token alone can't know a user was deleted after
    the token was issued — get_current_user's DB lookup is what
    actually catches this, so this test goes through the real
    endpoint, not just the decode function."""
    await _register()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        token = login_response.json()["access_token"]

    async with async_session_factory() as session:
        await session.execute(delete(User).where(User.email == TEST_EMAIL))
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
