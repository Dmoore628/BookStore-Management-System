from decimal import Decimal

import pytest

from bookstore.models.enums import PaymentMethod
from bookstore.services.checkout import CheckoutError, quote_cart


def test_quote_matches_known_tax() -> None:
    result = quote_cart(
        [(Decimal("10.00"), 2)],
        payment_method=PaymentMethod.CARD,
        tax_rate=Decimal("0.07"),
    )
    assert result.subtotal == Decimal("20.00")
    assert result.tax == Decimal("1.40")
    assert result.total == Decimal("21.40")
    assert result.change is None


def test_cash_requires_tender() -> None:
    with pytest.raises(CheckoutError):
        quote_cart(
            [(Decimal("10.00"), 1)],
            payment_method=PaymentMethod.CASH,
            tax_rate=Decimal("0.07"),
        )


def test_cash_with_tender_returns_change() -> None:
    result = quote_cart(
        [(Decimal("10.00"), 1)],
        payment_method=PaymentMethod.CASH,
        tax_rate=Decimal("0.07"),
        tender=Decimal("20.00"),
    )
    assert result.total == Decimal("10.70")
    assert result.change == Decimal("9.30")
