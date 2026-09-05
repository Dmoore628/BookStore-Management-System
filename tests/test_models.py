from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bookstore.models.entities import Book, Cart, CartLine, StockMovement
from bookstore.models.enums import StockReason


def test_book_defaults(db: Session) -> None:
    book = Book(title="t", author="a", isbn="isbn-1", price=Decimal("1.00"))
    db.add(book)
    db.flush()
    assert book.active is True
    assert book.quantity == 0
    assert book.created_at is not None


def test_stockmovement_relationship(db: Session) -> None:
    book = Book(title="t", author="a", isbn="isbn-2", price=Decimal("1.00"), quantity=3)
    db.add(book)
    db.flush()
    db.add(StockMovement(book_id=book.id, delta=3, reason=StockReason.INITIAL))
    db.flush()
    db.refresh(book)
    assert len(book.movements) == 1
    assert book.movements[0].reason is StockReason.INITIAL


def test_cartline_unique_per_cart_book(db: Session) -> None:
    book = Book(title="t", author="a", isbn="isbn-3", price=Decimal("1.00"), quantity=5)
    cart = Cart(session_id="sess-1")
    db.add_all([book, cart])
    db.flush()
    db.add(CartLine(cart_id=cart.id, book_id=book.id, quantity=1))
    db.flush()
    db.add(CartLine(cart_id=cart.id, book_id=book.id, quantity=1))
    with pytest.raises(IntegrityError):
        db.flush()
