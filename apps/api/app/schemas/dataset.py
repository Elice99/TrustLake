"""
Dataset request/response schemas. Metadata only — no file content is
ever part of a schema (file bytes live in object storage). storage_key
is deliberately NOT exposed: it's an internal detail clients don't need.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.profile import DatasetProfile


class DatasetCreate(BaseModel):
    name: str


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    created_at: datetime


class DatasetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None
    size_bytes: int
    content_sha256: str
    created_at: datetime


class DatasetDetail(BaseModel):
    """A dataset with its latest version and that version's profile."""

    dataset: DatasetRead
    version: DatasetVersionRead
    profile: DatasetProfile
