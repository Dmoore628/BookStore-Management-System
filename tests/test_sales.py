from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from bookstore.models.entities import Sale
from bookstore.models.enums import PaymentMethod
from bookstore.services import sales

TZ = "America/Denver"


def _sale(total: str, method: PaymentMethod, when: datetime) -> Sale:
    amount = Decimal(total)
    return Sale(
        payment_method=method,
        subtotal=amount,
        tax=Decimal("0.00"),
        total=amount,
        created_at=when,
    )


def test_daily_totals_split_cash_card(db: Session) -> None:
    day = date(2026, 9, 10)
    noon_utc = datetime(2026, 9, 10, 18, 0, 0)  # ~noon in Denver
    db.add(_sale("10.00", PaymentMethod.CASH, noon_utc))
    db.add(_sale("5.00", PaymentMethod.CARD, noon_utc))
    db.flush()
    totals = sales.daily_totals(db, day, TZ)
    assert totals.cash_total == Decimal("10.00")
    assert totals.card_total == Decimal("5.00")
    assert totals.total == Decimal("15.00")
    assert totals.count == 2


def test_sale_near_midnight_uses_store_tz(db: Session) -> None:
    # 05:30 UTC == 23:30 previous day in Denver (MDT, UTC-6).
    db.add(_sale("7.00", PaymentMethod.CASH, datetime(2026, 9, 10, 5, 30, 0)))
    db.flush()
    assert sales.daily_totals(db, date(2026, 9, 9), TZ).count == 1
    assert sales.daily_totals(db, date(2026, 9, 10), TZ).count == 0
