"""Database engine, session factory, and declarative base.

Dialect-aware: SQLite for local dev/tests, PostgreSQL (Neon) for staging/prod.
Foreign keys are enforced on SQLite via a PRAGMA so tests exercise the same
referential integrity as production.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from bookstore.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def make_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine appropriate for the configured database."""
    settings = get_settings()
    resolved = url or settings.database_url
    connect_args: dict[str, Any] = {}
    if resolved.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(resolved, connect_args=connect_args, future=True, pool_pre_ping=True)

    if resolved.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_fk(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _session_factory() -> sessionmaker[Session]:
    global _engine, _SessionLocal
    if _SessionLocal is None:
        _engine = make_engine()
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _SessionLocal


def get_engine() -> Engine:
    """Return (creating if needed) the process engine."""
    _session_factory()
    assert _engine is not None
    return _engine


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a session and always close it."""
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()
