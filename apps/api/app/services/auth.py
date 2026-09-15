"""
Auth service layer — business logic only, no FastAPI/HTTP awareness.
Route handlers translate exceptions raised here into HTTP responses.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import AuditEvent, User


class EmailAlreadyRegisteredError(Exception):
    pass


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    """Creates a new user and an audit_events row in the same session —
    get_db() commits both atomically once the calling route returns,
    per the architecture doc's transactional-audit-logging requirement.

    Checks for an existing email before inserting (fast, clean error
    for the common case), but the database's own unique constraint on
    users.email is the real backstop against a race condition where two
    identical registrations land at the same instant — that path isn't
    handled here yet (it would surface as a raw IntegrityError) and is
    a known gap, not an oversight, for now."""
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError(f"{email} is already registered")

    user = User(email=email, hashed_password=hash_password(password))
    session.add(user)
    await session.flush()  # assigns user.id without committing yet

    session.add(
        AuditEvent(
            actor_id=user.id,
            action="user_registered",
            entity_type="user",
            entity_id=user.id,
            event_metadata={"email": email},
        )
    )

    return user
