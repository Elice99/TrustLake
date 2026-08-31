"""
Settings loaded from environment variables / .env.

Deliberately has no default values for required fields. If a required
variable is missing, pydantic-settings raises a ValidationError at import
time — the app crashes immediately with a clear message instead of
starting up with a missing/blank secret. This is the Stage 0 requirement:
"Backend fails fast with a clear error message if a required env var is
missing — never silently defaults a secret."
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str


# Instantiated at import time so a missing var fails on startup,
# not on first use deep in a request handler.
settings = Settings()
