"""Shared pytest fixtures.

Required secrets are injected into the environment *before* any application module
is imported, so settings validate cleanly. Each test gets an isolated in-memory
SQLite database.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from decimal import Decimal

from cryptography.fernet import Fernet

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-0123456789")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("TAX_RATE_BPS", "700")
os.environ.setdefault("STORE_TZ", "America/Denver")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
import httpx
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import bookstore.models  # noqa: E402,F401  (registers tables on Base.metadata)
from bookstore.config import reset_settings_cache  # noqa: E402
from bookstore.database import Base, make_engine  # noqa: E402
from bookstore.models.entities import Book, User  # noqa: E402
from bookstore.models.enums import Role  # noqa: E402
from bookstore.security import hash_password  # noqa: E402
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

...

from sqlalchemy import create_engine
_TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
# Force table creation on the test engine specifically
from bookstore.models.entities import *  # noqa: F403
Base.metadata.create_all(_TEST_ENGINE)

@pytest.fixture
def db() -> Iterator[Session]:
    factory = sessionmaker(bind=_TEST_ENGINE, autoflush=False, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
async def client(db: Session) -> Iterator[httpx.AsyncClient]:
    from httpx import AsyncClient, ASGITransport
    from bookstore.main import app
    from bookstore.api.deps import get_db
    from bookstore.database import get_engine

    def _get_db_override():
        yield db
    
    def _get_engine_override():
        return _TEST_ENGINE

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_engine] = _get_engine_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

