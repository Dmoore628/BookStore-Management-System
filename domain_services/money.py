"""Money math — all currency handled as ``Decimal`` with half-up cent rounding.

Floats are never used for money. Rounding is ``ROUND_HALF_UP`` (standard retail
rounding). This module is pure and has no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


class MoneyError(Exception):
    """Base class for money-related domain errors."""


class InsufficientTender(MoneyError):
    """Raised when cash tendered is less than the amount due."""


def to_cents(amount: Decimal) -> Decimal:
    """Round ``amount`` to two decimal places, half-up."""
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(unit_price: Decimal, quantity: int) -> Decimal:
    """Return the rounded total for ``quantity`` units at ``unit_price``."""
    if quantity < 0:
        raise MoneyError("quantity must be non-negative")
    return to_cents(unit_price * quantity)


@dataclass(frozen=True)
class Quote:
    """An immutable price quote for a set of line items."""

    subtotal: Decimal
    tax: Decimal
    total: Decimal
    change: Decimal | None = None


def quote(
    lines: list[tuple[Decimal, int]],
    *,
    tax_rate: Decimal,
    tender: Decimal | None = None,
) -> Quote:
    """Compute subtotal, tax, total, and (optionally) change for ``lines``.

    ``lines`` is a list of ``(unit_price, quantity)`` tuples. If ``tender`` is
    provided it must be at least the total, or :class:`InsufficientTender` is
    raised; ``change`` is then the difference.
    """
    subtotal = to_cents(sum((line_total(p, q) for p, q in lines), Decimal("0")))
    tax = to_cents(subtotal * tax_rate)
    total = to_cents(subtotal + tax)

    change: Decimal | None = None
    if tender is not None:
        if tender < total:
            raise InsufficientTender(f"tender {tender} is less than total {total}")
        change = to_cents(tender - total)

    return Quote(subtotal=subtotal, tax=tax, total=total, change=change)

