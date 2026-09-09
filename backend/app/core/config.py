"""Application settings loaded from environment / .env.  [SEC-01][NFR-M3]

Secrets are never hardcoded; they come from the environment. `.env` is git-ignored.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://tableorder:changeme@db:5432/tableorder"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_timeout_seconds: int = 5

    # --- Auth / security ---
    jwt_secret: str = Field(default="dev-only-insecure-secret-change-me")
    jwt_expire_hours: int = 16
    bcrypt_rounds: int = 12

    # --- CORS (explicit origins only, no wildcard) [SEC-08] ---
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    # --- Rate limiting [SEC-11] ---
    login_rate_limit: int = 5
    login_rate_window_seconds: int = 60

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
