from decimal import Decimal

import pytest
from domain_services.money import (
    InsufficientTender,
    MoneyError,
    Quote,
    line_total,
    quote,
    to_cents,
)


def test_line_total_rounds_half_up() -> None:
    assert line_total(Decimal("12.995"), 2) == Decimal("25.99")


def test_line_total_rejects_negative_quantity() -> None:
    with pytest.raises(MoneyError):
        line_total(Decimal("1.00"), -1)


def test_to_cents_half_up() -> None:
    assert to_cents(Decimal("1.005")) == Decimal("1.01")


def test_quote_tax_and_change() -> None:
    result = quote(
        [(Decimal("10.00"), 2), (Decimal("5.50"), 1)],
        tax_rate=Decimal("0.07"),
        tender=Decimal("30.00"),
    )
    assert result == Quote(
        subtotal=Decimal("25.50"),
        tax=Decimal("1.79"),  # 25.50 * 0.07 = 1.785 -> 1.79 (half up)
        total=Decimal("27.29"),
        change=Decimal("2.71"),
    )


def test_quote_without_tender_has_no_change() -> None:
    result = quote([(Decimal("10.00"), 1)], tax_rate=Decimal("0.07"))
    assert result.change is None
    assert result.total == Decimal("10.70")


def test_quote_insufficient_tender_raises() -> None:
    with pytest.raises(InsufficientTender):
        quote([(Decimal("10.00"), 1)], tax_rate=Decimal("0.07"), tender=Decimal("5.00"))

