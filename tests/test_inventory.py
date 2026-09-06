from collections.abc import Callable
from decimal import Decimal

import pytest
from domain_services import inventory
from domain_services.entities import Book, StockMovement
from domain_services.enums import StockReason
from domain_services.inventory import BookNotFound, DuplicateISBN, InventoryError
from sqlalchemy.orm import Session


def test_add_book_records_initial_movement(db: Session) -> None:
    book = inventory.add_book(
        db, title="Clean Code", author="Martin", isbn="A1", price=Decimal("30.00"), quantity=4
    )
    assert book.quantity == 4
    movements = db.query(StockMovement).filter_by(book_id=book.id).all()
    assert [m.reason for m in movements] == [StockReason.INITIAL]


def test_duplicate_isbn_rejected(db: Session) -> None:
    inventory.add_book(db, title="A", author="B", isbn="DUP", price=Decimal("1.00"))
    with pytest.raises(DuplicateISBN):
        inventory.add_book(db, title="C", author="D", isbn="DUP", price=Decimal("2.00"))


def test_edit_does_not_change_quantity(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=7)
    inventory.edit_book(db, book.id, title="New Title", price=Decimal("9.99"))
    assert book.title == "New Title"
    assert book.price == Decimal("9.99")
    assert book.quantity == 7


def test_receive_increments_via_movement(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=2)
    inventory.receive_stock(db, book.id, 5)
    assert book.quantity == 7
    assert any(m.reason is StockReason.RECEIVE for m in book.movements)


def test_correction_adjusts_quantity(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=10)
    inventory.correct_stock(db, book.id, 8)
    assert book.quantity == 8
    correction = [m for m in book.movements if m.reason is StockReason.CORRECTION][0]
    assert correction.delta == -2


def test_deactivate(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book()
    inventory.deactivate(db, book.id)
    assert book.active is False


def test_try_decrement_success(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=3)
    assert inventory.try_decrement(db, book.id, 2) is True
    db.refresh(book)
    assert book.quantity == 1
    assert any(m.reason is StockReason.SALE for m in book.movements)


def test_try_decrement_insufficient_returns_false(
    db: Session, make_book: Callable[..., Book]
) -> None:
    book = make_book(quantity=1)
    assert inventory.try_decrement(db, book.id, 2) is False
    db.refresh(book)
    assert book.quantity == 1


def test_receive_missing_book_raises(db: Session) -> None:
    with pytest.raises(BookNotFound):
        inventory.receive_stock(db, 999, 1)


def test_receive_non_positive_rejected(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book()
    with pytest.raises(InventoryError):
        inventory.receive_stock(db, book.id, 0)


def test_search_matches_title_author_isbn(db: Session, make_book: Callable[..., Book]) -> None:
    make_book(title="Domain Driven Design", author="Evans", isbn="DDD-1")
    assert len(inventory.search(db, "Evans")) == 1
    assert len(inventory.search(db, "DDD")) == 1
    assert len(inventory.search(db, "nothing")) == 0

