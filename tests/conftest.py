"""Shared pytest fixtures.

Required secrets are injected into the environment *before* any application module
is imported, so settings validate cleanly. Each test gets an isolated in-memory
SQLite database.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from cryptography.fernet import Fernet

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-0123456789")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("TAX_RATE_BPS", "700")
os.environ.setdefault("STORE_TZ", "America/Denver")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import domain_services.entities  # noqa: E402,F401  (registers tables on Base.metadata)
import httpx
import pytest  # noqa: E402
from domain_services.database import Base  # noqa: E402
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

...

_TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
# Force table creation on the test engine specifically
from domain_services.entities import *  # noqa: F403

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
    from api_server.deps import get_db
    from api_server.main import app
    from domain_services.database import get_engine
    from httpx import ASGITransport, AsyncClient

    def _get_db_override():
        yield db
    
    def _get_engine_override():
        return _TEST_ENGINE

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_engine] = _get_engine_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


