from collections.abc import Callable
from decimal import Decimal

import pytest
from domain_services import cart
from domain_services.cart import EmptyCart, InsufficientStock
from domain_services.entities import Book, Sale
from domain_services.enums import PaymentMethod
from sqlalchemy.orm import Session

TAX = Decimal("0.07")


def _cart(db: Session):
    return cart.get_or_create_cart(db, "session-xyz")


def test_add_line_merges_quantity(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=10)
    c = _cart(db)
    cart.add_line(db, c, book.id, 2)
    cart.add_line(db, c, book.id, 3)
    assert len(c.lines) == 1
    assert c.lines[0].quantity == 5


def test_add_beyond_stock_blocked(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=2)
    c = _cart(db)
    with pytest.raises(InsufficientStock):
        cart.add_line(db, c, book.id, 3)


def test_set_quantity_zero_removes(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=5)
    c = _cart(db)
    cart.add_line(db, c, book.id, 2)
    cart.set_quantity(db, c, book.id, 0)
    assert c.lines == []


def test_cart_totals_live(db: Session, make_book: Callable[..., Book]) -> None:
    a = make_book(isbn="A", price="10.00", quantity=5)
    b = make_book(isbn="B", price="5.00", quantity=5)
    c = _cart(db)
    cart.add_line(db, c, a.id, 2)
    cart.add_line(db, c, b.id, 1)
    totals = cart.totals(db, c, tax_rate=TAX)
    assert totals.subtotal == Decimal("25.00")
    assert totals.tax == Decimal("1.75")
    assert totals.total == Decimal("26.75")


def test_checkout_atomic_creates_sale_and_decrements(
    db: Session, make_book: Callable[..., Book]
) -> None:
    a = make_book(isbn="A", price="10.00", quantity=5)
    b = make_book(isbn="B", price="5.00", quantity=5)
    c = _cart(db)
    cart.add_line(db, c, a.id, 2)
    cart.add_line(db, c, b.id, 1)
    sale = cart.checkout(
        db, c, payment_method=PaymentMethod.CASH, tax_rate=TAX, tender=Decimal("30.00")
    )
    assert sale.total == Decimal("26.75")
    assert sale.change == Decimal("3.25")
    assert len(sale.lines) == 2
    db.refresh(a)
    db.refresh(b)
    assert a.quantity == 3
    assert b.quantity == 4
    assert c.lines == []


def test_checkout_empty_rejected(db: Session) -> None:
    c = _cart(db)
    with pytest.raises(EmptyCart):
        cart.checkout(db, c, payment_method=PaymentMethod.CARD, tax_rate=TAX)


def test_checkout_rolls_back_if_any_line_short(
    db: Session, make_book: Callable[..., Book]
) -> None:
    plenty = make_book(isbn="A", price="10.00", quantity=5)
    scarce = make_book(isbn="B", price="5.00", quantity=1)
    c = _cart(db)
    cart.add_line(db, c, plenty.id, 2)
    cart.add_line(db, c, scarce.id, 1)
    # Simulate the last copy being corrected away after it was added to the cart.
    scarce.quantity = 0
    db.flush()
    with pytest.raises(InsufficientStock):
        cart.checkout(
            db, c, payment_method=PaymentMethod.CASH, tax_rate=TAX, tender=Decimal("50.00")
        )
    db.refresh(plenty)
    assert plenty.quantity == 5  # nothing decremented
    assert db.query(Sale).count() == 0

