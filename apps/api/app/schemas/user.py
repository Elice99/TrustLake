"""
User request/response schemas.

UserCreate takes a plaintext password (from the future /auth/register
endpoint, Stage 2 Day 4) — hashing happens in the service layer, never
here. UserRead deliberately excludes hashed_password; there is no
schema anywhere that would let a hashed password leak into an API
response.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime
