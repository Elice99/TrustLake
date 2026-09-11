"""
Model integration tests — real inserts/queries against a live database,
matching the roadmap's requirement to use a real test database, not
mocks, for the DB layer.

Each test wraps its work in a transaction that's rolled back at the
end, so these don't leave test data behind in a database that's shared
across test runs.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import async_session_factory
from app.models import AuditEvent, Dataset, User


async def test_create_and_read_user() -> None:
    async with async_session_factory() as session, session.begin():
        user = User(email="test-day3@example.com", hashed_password="not-a-real-hash")
        session.add(user)
        await session.flush()

        assert user.id is not None
        assert user.created_at is not None

        result = await session.execute(select(User).where(User.id == user.id))
        fetched = result.scalar_one()
        assert fetched.email == "test-day3@example.com"

        await session.rollback()


async def test_duplicate_email_rejected() -> None:
    async with async_session_factory() as session:
        session.add(User(email="dup-day3@example.com", hashed_password="x"))
        await session.flush()

        session.add(User(email="dup-day3@example.com", hashed_password="y"))
        try:
            await session.flush()
            raised = False
        except IntegrityError:
            raised = True
        finally:
            await session.rollback()

        assert raised, "duplicate email should violate the unique constraint"


async def test_dataset_requires_valid_owner() -> None:
    async with async_session_factory() as session, session.begin():
        user = User(email="owner-day3@example.com", hashed_password="x")
        session.add(user)
        await session.flush()

        dataset = Dataset(name="test dataset", owner_id=user.id)
        session.add(dataset)
        await session.flush()

        assert dataset.owner_id == user.id

        await session.rollback()


async def test_audit_event_allows_null_actor_and_stores_jsonb() -> None:
    async with async_session_factory() as session, session.begin():
        event = AuditEvent(
            actor_id=None,
            action="dataset_uploaded",
            entity_type="dataset",
            entity_id=uuid.uuid4(),
            event_metadata={"filename": "test.csv", "size_bytes": 1024},
        )
        session.add(event)
        await session.flush()

        result = await session.execute(
            select(AuditEvent).where(AuditEvent.id == event.id)
        )
        fetched = result.scalar_one()
        assert fetched.actor_id is None
        assert fetched.event_metadata == {"filename": "test.csv", "size_bytes": 1024}

        await session.rollback()
