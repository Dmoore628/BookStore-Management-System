"""Checkout quoting — turns cart line prices into a priced :class:`Quote`.

Encodes the payment rules: cash requires tender (and yields change); card does not.
"""

from __future__ import annotations

from decimal import Decimal

from bookstore.models.enums import PaymentMethod
from bookstore.services.money import Quote, quote


class CheckoutError(Exception):
    """Raised when checkout inputs violate payment rules."""


def quote_cart(
    lines: list[tuple[Decimal, int]],
    *,
    payment_method: PaymentMethod,
    tax_rate: Decimal,
    tender: Decimal | None = None,
) -> Quote:
    """Quote a set of ``(unit_price, quantity)`` lines for a payment method."""
    if payment_method is PaymentMethod.CASH:
        if tender is None:
            raise CheckoutError("cash payment requires a tender amount")
        return quote(lines, tax_rate=tax_rate, tender=tender)
    return quote(lines, tax_rate=tax_rate, tender=None)
