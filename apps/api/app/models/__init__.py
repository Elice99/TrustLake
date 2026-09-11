"""
Every model must be imported here (not just defined in its own file).
SQLAlchemy's declarative registry only knows about a model once its
module has been imported somewhere — Alembic's autogenerate walks
Base.metadata, which is only populated by models that have actually
been imported into the running process.
"""

from app.models.audit_event import AuditEvent
from app.models.dataset import Dataset
from app.models.user import User

__all__ = ["User", "Dataset", "AuditEvent"]
