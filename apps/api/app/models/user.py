"""
User model.

The architecture doc (§4.2) only specifies "users — auth identity",
without listing fields. Kept deliberately minimal here: id, email,
hashed_password, created_at — the smallest set an auth system actually
needs (Stage 2 Days 4-5). Nothing else (e.g. display name, is_active)
is added without being asked for.
"""

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
