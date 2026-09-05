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
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import bookstore.models  # noqa: E402,F401  (registers tables on Base.metadata)
from bookstore.config import reset_settings_cache  # noqa: E402
from bookstore.database import Base, make_engine  # noqa: E402
from bookstore.models.entities import Book, User  # noqa: E402
from bookstore.models.enums import Role  # noqa: E402
from bookstore.security import hash_password  # noqa: E402

reset_settings_cache()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def make_book(db: Session) -> Callable[..., Book]:
    def _make(
        *,
        title: str = "The Pragmatic Programmer",
        author: str = "Hunt & Thomas",
        isbn: str | None = None,
        price: str = "39.99",
        quantity: int = 10,
    ) -> Book:
        book = Book(
            title=title,
            author=author,
            isbn=isbn or f"ISBN-{title[:6]}-{quantity}-{price}",
            price=Decimal(price),
            quantity=quantity,
        )
        db.add(book)
        db.flush()
        return book

    return _make


@pytest.fixture
def owner(db: Session) -> User:
    user = User(username="damian", password_hash=hash_password("owner-pass"), role=Role.OWNER)
    db.add(user)
    db.flush()
    return user
