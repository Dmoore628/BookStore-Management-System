"""Inventory service.

Books are edited without ever touching quantity directly. Quantity changes flow
through an append-only :class:`StockMovement` ledger, and ``Book.quantity`` holds
the running total. Sales use :func:`try_decrement`, an atomic, oversell-safe
conditional update so two concurrent cashiers can never sell the same last copy.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any, cast

from domain_services.entities import Book, StockMovement
from domain_services.enums import StockReason
from sqlalchemy import CursorResult, or_, select, update
from sqlalchemy.orm import Session


class InventoryError(Exception):
    """Base class for inventory errors."""


class DuplicateISBN(InventoryError):
    """Raised when adding a book whose ISBN already exists."""


class BookNotFound(InventoryError):
    """Raised when a book id does not exist."""


def _require_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise BookNotFound(f"book {book_id} does not exist")
    return book


def add_book(
    db: Session,
    *,
    title: str,
    author: str,
    isbn: str,
    price: Decimal,
    quantity: int = 0,
    shelf_location: str = "",
    actor_id: int | None = None,
) -> Book:
    """Create a book. Initial stock (if any) is recorded as a ledger movement."""
    if db.scalar(select(Book).where(Book.isbn == isbn)) is not None:
        raise DuplicateISBN(f"a book with ISBN {isbn} already exists")
    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        price=price,
        quantity=quantity,
        shelf_location=shelf_location,
    )
    db.add(book)
    db.flush()
    if quantity:
        db.add(
            StockMovement(
                book_id=book.id, delta=quantity, reason=StockReason.INITIAL, actor_id=actor_id
            )
        )
    db.flush()
    return book


def edit_book(
    db: Session,
    book_id: int,
    *,
    title: str | None = None,
    author: str | None = None,
    price: Decimal | None = None,
    shelf_location: str | None = None,
) -> Book:
    """Edit descriptive fields. Quantity is intentionally not editable here."""
    book = _require_book(db, book_id)
    if title is not None:
        book.title = title
    if author is not None:
        book.author = author
    if price is not None:
        book.price = price
    if shelf_location is not None:
        book.shelf_location = shelf_location
    db.flush()
    return book


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def list_books(db: Session, *, include_inactive: bool = False) -> Sequence[Book]:
    stmt = select(Book).order_by(Book.title)
    if not include_inactive:
        stmt = stmt.where(Book.active.is_(True))
    return db.scalars(stmt).all()


def search(db: Session, term: str, *, include_inactive: bool = False) -> Sequence[Book]:
    like = f"%{term}%"
    stmt = select(Book).where(
        or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like))
    )
    if not include_inactive:
        stmt = stmt.where(Book.active.is_(True))
    return db.scalars(stmt.order_by(Book.title)).all()


def receive_stock(
    db: Session, book_id: int, quantity: int, *, actor_id: int | None = None, note: str = ""
) -> Book:
    """Increase stock by receiving a shipment (ledger movement + running total)."""
    if quantity <= 0:
        raise InventoryError("received quantity must be positive")
    book = _require_book(db, book_id)
    book.quantity += quantity
    db.add(
        StockMovement(
            book_id=book.id,
            delta=quantity,
            reason=StockReason.RECEIVE,
            actor_id=actor_id,
            note=note,
        )
    )
    db.flush()
    return book


def correct_stock(
    db: Session, book_id: int, new_quantity: int, *, actor_id: int | None = None, note: str = ""
) -> Book:
    """Set an absolute quantity (manager correction) and record the delta."""
    if new_quantity < 0:
        raise InventoryError("corrected quantity must be non-negative")
    book = _require_book(db, book_id)
    delta = new_quantity - book.quantity
    book.quantity = new_quantity
    db.add(
        StockMovement(
            book_id=book.id,
            delta=delta,
            reason=StockReason.CORRECTION,
            actor_id=actor_id,
            note=note,
        )
    )
    db.flush()
    return book


def deactivate(db: Session, book_id: int) -> Book:
    """Soft-delete a book (keeps sales history intact)."""
    book = _require_book(db, book_id)
    book.active = False
    db.flush()
    return book


def try_decrement(db: Session, book_id: int, quantity: int, *, actor_id: int | None = None) -> bool:
    """Atomically decrement stock if enough is available.

    Returns True and records a SALE movement when the decrement succeeds, or
    False (no change) when stock is insufficient. Safe against concurrent sales.
    """
    if quantity <= 0:
        raise InventoryError("decrement quantity must be positive")
    result = cast(
        CursorResult[Any],
        db.execute(
            update(Book)
            .where(Book.id == book_id, Book.quantity >= quantity)
            .values(quantity=Book.quantity - quantity)
        ),
    )
    if result.rowcount != 1:
        return False
    db.add(
        StockMovement(
            book_id=book_id, delta=-quantity, reason=StockReason.SALE, actor_id=actor_id
        )
    )
    db.flush()
    return True

