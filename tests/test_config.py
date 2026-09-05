from decimal import Decimal

import pytest
from pydantic import ValidationError

from bookstore.config import Settings


def test_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAX_RATE_BPS", "700")
    monkeypatch.setenv("STORE_TZ", "America/New_York")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.tax_rate == Decimal("0.07")
    assert settings.store_tz == "America/New_York"


def test_tax_rate_derives_from_basis_points(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAX_RATE_BPS", "725")
    assert Settings(_env_file=None).tax_rate == Decimal("0.0725")  # type: ignore[call-arg]


def test_missing_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_negative_tax_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAX_RATE_BPS", "-1")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_is_sqlite_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./x.db")
    assert Settings(_env_file=None).is_sqlite is True  # type: ignore[call-arg]
