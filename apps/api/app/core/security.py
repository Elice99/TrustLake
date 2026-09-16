"""
Password hashing and JWT handling.

argon2 (not bcrypt, never plaintext) per the roadmap's explicit
Stage 2 requirement. argon2 is the current recommended algorithm for
new applications — it won the Password Hashing Competition and is
designed specifically to resist GPU/ASIC-accelerated cracking attempts
better than older algorithms.

PasswordHasher() with default parameters is intentional here — the
defaults are already tuned by the argon2-cffi maintainers to current
security recommendations. Don't hand-tune time_cost/memory_cost
without a specific, documented reason.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        _hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID) -> str:
    """Encodes the user's ID as the JWT "subject" (sub) claim — the
    standard JWT field for "who is this token about". exp is the
    expiration timestamp; pyjwt itself enforces this on decode, we
    don't need to check it manually."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> uuid.UUID:
    """Returns the user ID encoded in a valid, unexpired token. Raises
    InvalidTokenError for anything wrong with the token — expired,
    tampered with, malformed, wrong signature — so the caller (the
    get_current_user dependency) can turn any of these into a uniform
    401, without needing to know pyjwt's specific exception types."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise InvalidTokenError("Invalid or expired token") from exc
