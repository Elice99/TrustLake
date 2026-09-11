"""
AuditEvent model — append-only audit log.

Per Architecture doc §4.2: "audit_events — append-only; actor_id,
action, entity_type, entity_id, metadata (jsonb), created_at."

Two things worth calling out:

1. The Python attribute is named `event_metadata`, not `metadata` —
   SQLAlchemy's declarative Base reserves `metadata` for its own schema
   registry (Base.metadata), so a model can't use that name for a
   column attribute. The actual database column is still named
   `metadata`, exactly as specified, via mapped_column("metadata", ...).

2. actor_id is nullable. This isn't explicitly specified either way in
   the architecture doc. Judgment call: some audited actions (e.g. a
   background job, or preserving history after a user is deleted)
   may not have a live user to attribute the action to, so forcing
   non-null risks blocking legitimate system-generated events. No
   foreign key constraint to users.id either, for the same reason —
   an audit record should survive independently of the referenced
   user still existing.
"""

import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_events"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(nullable=False)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
