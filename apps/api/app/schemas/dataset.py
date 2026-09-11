"""
Dataset request/response schemas. Metadata-only, matching the model —
no file content is ever part of this schema (see app/models/dataset.py
for why: file bytes live in object storage, not Postgres).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetCreate(BaseModel):
    name: str


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    created_at: datetime
