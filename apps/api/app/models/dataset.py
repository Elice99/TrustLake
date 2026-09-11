"""
Dataset model — top-level record only.

Per Architecture doc §4.2: "datasets — top-level dataset record (name,
owner, created_at)". This is metadata only, per PRD §45/§46 — the
actual file bytes live in object storage, not here. Version history
(dataset_versions), profiling results, and Trust Scores are separate
tables belonging to later stages (Stage 3+), not built yet.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class Dataset(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
