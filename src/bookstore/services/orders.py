"""Supplier order tracking.

Orders start ``PENDING``. Receiving an order increments stock for every line via
the inventory ledger and flips the status to ``RECEIVED`` exactly once.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from domain_services import inventory
from domain_services.entities import SupplierOrder, SupplierOrderLine
from domain_services.enums import OrderStatus
from sqlalchemy import select
from sqlalchemy.orm import Session


class OrderError(Exception):
    """Raised on invalid supplier-order operations."""


def create_order(
    db: Session, *, supplier: str, lines: list[tuple[int, int]]
) -> SupplierOrder:
    """Create a pending order. ``lines`` is a list of ``(book_id, quantity)``."""
    if not lines:
        raise OrderError("an order must have at least one line")
    order = SupplierOrder(supplier=supplier, status=OrderStatus.PENDING)
    db.add(order)
    db.flush()
    for book_id, quantity in lines:
        if quantity <= 0:
            raise OrderError("order line quantity must be positive")
        db.add(SupplierOrderLine(order_id=order.id, book_id=book_id, quantity=quantity))
    db.flush()
    return order


def list_orders(db: Session, *, status: OrderStatus | None = None) -> Sequence[SupplierOrder]:
    stmt = select(SupplierOrder).order_by(SupplierOrder.created_at.desc())
    if status is not None:
        stmt = stmt.where(SupplierOrder.status == status)
    return db.scalars(stmt).all()


def receive_order(db: Session, order_id: int, *, actor_id: int | None = None) -> SupplierOrder:
    """Receive a pending order: increment stock per line, mark RECEIVED once."""
    order = db.get(SupplierOrder, order_id)
    if order is None:
        raise OrderError(f"order {order_id} does not exist")
    if order.status is not OrderStatus.PENDING:
        raise OrderError(f"order {order_id} is {order.status}, cannot receive")
    for line in order.lines:
        inventory.receive_stock(
            db, line.book_id, line.quantity, actor_id=actor_id, note=f"order #{order.id}"
        )
    order.status = OrderStatus.RECEIVED
    order.received_at = datetime.now(UTC).replace(tzinfo=None)
    db.flush()
    return order

