"""Application configuration.

Every runtime value comes from the environment (or a documented dev default) —
never a hardcoded constant buried in business logic. Secrets have no defaults and
must be supplied, so the app refuses to start misconfigured.
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASIS_POINTS = Decimal(10000)


class Settings(BaseSettings):
    """Typed, validated application settings sourced from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Ledger & Spine"
    environment: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # --- Persistence ---
    database_url: str = "sqlite:///./bookstore_dev.db"

    # --- Secrets (no defaults on purpose) ---
    secret_key: str = Field(min_length=16)
    encryption_key: str

    # --- Store policy (configuration, not code constants) ---
    tax_rate_bps: int = 725
    store_tz: str = "America/Denver"
    currency: str = "USD"
    low_stock_threshold: int = 3

    # --- Schema bootstrap (dev/demo convenience; migrations own prod schema) ---
    auto_create_schema: bool = True

    # --- Backups ---
    backup_destination: str = "file://./backups"

    # --- Session cookie ---
    session_cookie_name: str = "ls_session"
    session_https_only: bool = False
    session_max_age_seconds: int = 28800

    # --- Seed accounts ---
    initial_owner_username: str = "damian"
    initial_owner_password: str | None = None
    seed_manager_username: str = "richard"
    seed_manager_password: str | None = None
    seed_cashier_username: str = "stephen"
    seed_cashier_password: str | None = None

    @field_validator("tax_rate_bps")
    @classmethod
    def _non_negative_tax(cls, value: int) -> int:
        if value < 0:
            raise ValueError("tax_rate_bps must be >= 0")
        return value

    @property
    def tax_rate(self) -> Decimal:
        """Tax rate as a Decimal fraction (e.g. 725 bps -> Decimal('0.0725'))."""
        return Decimal(self.tax_rate_bps) / _BASIS_POINTS

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings (used by tests that mutate the environment)."""
    get_settings.cache_clear()

