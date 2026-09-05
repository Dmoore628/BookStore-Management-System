from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from bookstore.models.entities import Book
from bookstore.models.enums import OrderStatus
from bookstore.services import orders
from bookstore.services.orders import OrderError


def test_create_and_receive_increments_stock(
    db: Session, make_book: Callable[..., Book]
) -> None:
    book = make_book(quantity=1)
    order = orders.create_order(db, supplier="Penguin", lines=[(book.id, 5)])
    assert order.status is OrderStatus.PENDING
    orders.receive_order(db, order.id)
    db.refresh(book)
    assert book.quantity == 6
    assert order.status is OrderStatus.RECEIVED
    assert order.received_at is not None


def test_cannot_receive_twice(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=0)
    order = orders.create_order(db, supplier="X", lines=[(book.id, 1)])
    orders.receive_order(db, order.id)
    with pytest.raises(OrderError):
        orders.receive_order(db, order.id)


def test_empty_order_rejected(db: Session) -> None:
    with pytest.raises(OrderError):
        orders.create_order(db, supplier="X", lines=[])


def test_list_orders_filters_by_status(db: Session, make_book: Callable[..., Book]) -> None:
    book = make_book(quantity=0)
    orders.create_order(db, supplier="A", lines=[(book.id, 1)])
    assert len(orders.list_orders(db, status=OrderStatus.PENDING)) == 1
    assert len(orders.list_orders(db, status=OrderStatus.RECEIVED)) == 0
