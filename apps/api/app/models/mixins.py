"""
Shared model mixins.

UUID primary keys (not auto-increment integers) per the Stage 2 Day 3
decision: avoids leaking sequential record counts, and matches this
being a portfolio-grade product per the PRD's stated philosophy.

UUIDs are generated client-side (Python's uuid.uuid4, not Postgres'
gen_random_uuid()) — this avoids any dependency on a Postgres extension
being enabled, and generates identically whether the row is being
built in a real DB session or a plain Python object in a unit test.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
