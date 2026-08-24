import os

from app.core.config import Settings


def test_default_database_uses_sqlite_when_env_is_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    settings = Settings()
    assert settings.database_url.startswith("sqlite+")
    assert settings.redis_url.startswith("redis://")
