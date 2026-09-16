"""
Shared FastAPI dependencies for the v1 API — currently just auth.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db
from app.models import User

# tokenUrl points Swagger UI's "Authorize" button at the real login
# endpoint, so /docs can be used to log in and test protected routes
# interactively, not just as documentation.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(_oauth2_scheme),  # noqa: B008 — FastAPI's DI pattern
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> User:
    """Decodes the bearer token and loads the real user it refers to.
    A single 401 covers every failure mode (missing token, expired,
    tampered, or referring to a user that no longer exists) — the
    client doesn't get information about *why* it failed beyond
    "not authenticated", which is the standard, safe approach."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(token)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise unauthorized

    return user
