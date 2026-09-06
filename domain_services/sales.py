"""Daily sales log — timezone-aware bucketing.

Timestamps are stored as naive UTC. "Today's sales" is computed against a
configurable store timezone so totals are correct near midnight, regardless of
the server's UTC clock.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from domain_services.entities import Sale
from domain_services.enums import PaymentMethod
from sqlalchemy import select
from sqlalchemy.orm import Session


def _utc_bounds(day: date, tz: str) -> tuple[datetime, datetime]:
    """Return the [start, end) naive-UTC bounds for a local ``day`` in ``tz``."""
    zone = ZoneInfo(tz)
    start_local = datetime.combine(day, time.min, tzinfo=zone)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return start_utc, end_utc


def list_sales(db: Session, day: date, tz: str) -> Sequence[Sale]:
    """All sales whose local (store-tz) date equals ``day``."""
    start, end = _utc_bounds(day, tz)
    stmt = (
        select(Sale)
        .where(Sale.created_at >= start, Sale.created_at < end)
        .order_by(Sale.created_at)
    )
    return db.scalars(stmt).all()


@dataclass(frozen=True)
class DailyTotals:
    day: date
    cash_total: Decimal
    card_total: Decimal
    total: Decimal
    count: int


def daily_totals(db: Session, day: date, tz: str) -> DailyTotals:
    """Aggregate cash/card/total sales for a local ``day``."""
    sales = list_sales(db, day, tz)
    cash = sum(
        (s.total for s in sales if s.payment_method is PaymentMethod.CASH), Decimal("0.00")
    )
    card = sum(
        (s.total for s in sales if s.payment_method is PaymentMethod.CARD), Decimal("0.00")
    )
    return DailyTotals(
        day=day,
        cash_total=Decimal(cash),
        card_total=Decimal(card),
        total=Decimal(cash) + Decimal(card),
        count=len(sales),
    )

