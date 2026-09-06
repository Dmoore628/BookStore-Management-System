"""Backups — serverless-safe, pluggable destination.

Serializes every table to JSON and writes it to a configurable destination URI so
it never assumes a writable local filesystem in production:

- ``file://<path>``  — local directory (development)
- ``blob://<...>``   — object storage (wired in deployment phase)
- ``neon://<...>``   — managed Postgres export (wired in deployment phase)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from domain_services.config import get_settings
from domain_services.database import Base
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

_TABLE_ORDER = [
    "users",
    "books",
    "stock_movements",
    "carts",
    "cart_lines",
    "sales",
    "sale_lines",
    "supplier_orders",
    "supplier_order_lines",
    "customer_requests",
]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_backup_payload(db: Session) -> dict[str, list[dict[str, Any]]]:
    """Return a JSON-serializable snapshot of every table."""
    mappers = {m.class_.__tablename__: m for m in Base.registry.mappers}
    payload: dict[str, list[dict[str, Any]]] = {}
    for table_name in _TABLE_ORDER:
        mapper = mappers[table_name]
        columns = [c.key for c in inspect(mapper).columns]
        rows: list[dict[str, Any]] = []
        for obj in db.scalars(select(mapper.class_)).all():
            rows.append({col: _jsonable(getattr(obj, col)) for col in columns})
        payload[table_name] = rows
    return payload


@dataclass(frozen=True)
class BackupResult:
    location: str
    table_count: int
    row_count: int


def run_backup(db: Session, *, destination: str | None = None) -> BackupResult:
    """Write a full backup to ``destination`` (defaults to configured value)."""
    dest = destination or get_settings().backup_destination
    payload = build_backup_payload(db)
    body = json.dumps(payload, indent=2, sort_keys=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"backup-{stamp}.json"

    if dest.startswith("file://"):
        directory = Path(dest[len("file://") :])
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / filename
        target.write_text(body, encoding="utf-8")
        location = str(target)
    else:  # pragma: no cover - remote destinations wired in deployment phase
        raise NotImplementedError(f"backup destination not supported yet: {dest}")

    return BackupResult(
        location=location,
        table_count=len(payload),
        row_count=sum(len(rows) for rows in payload.values()),
    )

