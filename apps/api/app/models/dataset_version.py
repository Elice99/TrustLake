"""
DatasetVersion model — one row per version of a dataset's file.

Version 1 is the original upload and is NEVER modified or overwritten
(PRD sections 13 and 39). Every later transformation creates a new row
(parent_version_id points at the version it was derived from) with its
own file in object storage. Rows here are only ever inserted, never
updated.

storage_key is the object key inside the configured bucket (e.g.
"datasets/<dataset>/versions/<version>/original.csv"), not a full URI —
the StorageProvider abstraction works in keys. It never contains any
user-supplied text, so a filename can't influence where a file lands.

content_sha256 is the SHA-256 of the exact bytes uploaded. It lets us
prove later that the stored original is still byte-identical.
"""

import uuid

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class DatasetVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id", "version_number", name="uq_dataset_versions_dataset_version"
        ),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_versions.id"), nullable=True
    )
    storage_key: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
