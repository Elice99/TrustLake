"""
AuditEvent response schema. No Create schema — audit events are always
written internally by the services that perform an action, never
accepted as direct user input.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    event_metadata: dict[str, Any] | None
    created_at: datetime
