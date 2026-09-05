"""
Stage 0 smoke tests.

Real tests, not placeholders: they exercise the actual placeholder route
and confirm the fail-fast env validation (Stage 0's own verification
gate) genuinely works. Grows into real endpoint/integration tests from
Stage 2 onward.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app

client = TestClient(app)


def test_root_returns_hello_trustlake() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, TrustLake"}


def test_settings_fail_fast_on_missing_required_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirms Settings() raises rather than silently defaulting when a
    required var is missing — the exact behavior Stage 0's roadmap gate
    requires. _env_file=None disables reading any local .env file for
    this instantiation, so this test is correctly isolated even when a
    real .env (with a real DATABASE_URL) exists on disk, as it always
    will on a working dev machine."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "trustlake")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test")
    monkeypatch.setenv("POSTGRES_DB", "trustlake")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
