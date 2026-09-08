# Import every model module here as they're added (starting Day 3).
# SQLAlchemy's declarative registry only knows about a model once its
# module has been imported somewhere — alembic/env.py imports
# app.db.base.Base, but that alone won't pull in models defined in
# separate files unless something imports those files too. This module
# is that "something": e.g. `from app.models.user import User`.
