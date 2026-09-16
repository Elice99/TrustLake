"""
Settings loaded from environment variables / .env.

Deliberately has no default values for required fields. If a required
variable is missing, pydantic-settings raises a ValidationError at import
time — the app crashes immediately with a clear message instead of
starting up with a missing/blank secret. This is the Stage 0 requirement:
"Backend fails fast with a clear error message if a required env var is
missing — never silently defaults a secret."
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    # Signs and verifies JWTs. Required, no default — a hardcoded
    # fallback signing secret would mean anyone reading the source code
    # could forge valid tokens for any user. Generate a real one with:
    # python -c "import secrets; print(secrets.token_urlsafe(32))"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    # 30 minutes, per the Day 5 decision. No refresh-token mechanism
    # exists yet — when a token expires, the only way to get a new one
    # is to log in again. Acceptable for pre-MVP; revisit if/when this
    # moves toward handling real user sessions in production.
    jwt_expire_minutes: int = 30

    @field_validator("database_url")
    @classmethod
    def require_asyncpg_driver(cls, v: str) -> str:
        """SQLAlchemy's async engine requires an explicit driver in the
        URL scheme. A plain postgresql:// URL doesn't error clearly here
        — it fails later with a confusing driver-mismatch error at first
        query. Catching it here instead, at config-load time."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the postgresql+asyncpg:// scheme "
                "for the async engine (e.g. "
                "postgresql+asyncpg://user:pass@host:5432/db). "
                f"Got: {v.split('://')[0]}://..."
            )
        return v


# Instantiated at import time so a missing var fails on startup,
# not on first use deep in a request handler.
settings = Settings()
