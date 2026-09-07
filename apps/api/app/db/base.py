"""
Shared declarative base for all SQLAlchemy models.

Kept in its own module (not in session.py or a models/__init__.py) so
Alembic's env.py can import Base.metadata without also importing the
engine/session machinery, and so models/*.py files can import Base
without a circular import back to session.py.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
