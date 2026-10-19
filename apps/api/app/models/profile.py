"""
Profile model — the stored result of profiling one dataset version.

One row per dataset_version (unique). Stored so the profile is computed
once at upload, not recomputed on every page view. The profile column
holds the DatasetProfile schema as JSONB; profiler_version records which
version of the profiling definitions produced it.
"""

import uuid
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class Profile(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "profiles"

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id"),
        nullable=False,
        unique=True,
    )
    profiler_version: Mapped[int] = mapped_column(nullable=False)
    profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
