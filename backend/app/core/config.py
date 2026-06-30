"""
backend/app/core/config.py
───────────────────────────
Application settings loaded from environment variables via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "PeopleLens API"
    app_version: str = "0.1.0"
    env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql://peoplelens_user:peoplelens_dev_pass@localhost:5432/peoplelens"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "peoplelens"
    postgres_user: str = "peoplelens_user"
    postgres_password: str = "peoplelens_dev_pass"

    # Security
    api_secret_key: str = "dev-secret-key-replace-in-production"
    api_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Data paths
    data_dir: Path = Path("data")
    synthetic_data_dir: Path = Path("data/synthetic")
    models_dir: Path = Path("models")

    # CORS
    allowed_origins: list[str] = ["http://localhost:8501", "http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
