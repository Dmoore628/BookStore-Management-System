"""SQLAlchemy ORM entities.

Money is stored as ``Numeric(10, 2)`` and handled as ``Decimal`` everywhere.
Stock is never edited in place: every change is an append-only ``StockMovement``
row, and the ``Book.quantity`` column is the running total. The cart is
DB-backed (keyed by the signed session id) so it survives stateless requests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookstore.database import Base
from bookstore.models.enums import (
    OrderStatus,
    PaymentMethod,
    RequestStatus,
    Role,
    StockReason,
)


def _now() -> datetime:
    """Naive UTC timestamp.

    Stored values are UTC by convention (no tzinfo), which behaves identically on
    SQLite and PostgreSQL. Timezone-aware presentation is done at the edges.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255), index=True)
    isbn: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    shelf_location: Mapped[str] = mapped_column(String(64), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now
    )

    movements: Mapped[list[StockMovement]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[StockReason] = mapped_column(Enum(StockReason, native_enum=False, length=16))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    book: Mapped[Book] = relationship(back_populates="movements")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    lines: Mapped[list[CartLine]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartLine(Base):
    __tablename__ = "cart_lines"
    __table_args__ = (UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer)

    cart: Mapped[Cart] = relationship(back_populates="lines")
    book: Mapped[Book] = relationship()


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=8)
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tender: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    change: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, index=True
    )

    lines: Mapped[list[SaleLine]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )


class SaleLine(Base):
    __tablename__ = "sale_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    title: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    sale: Mapped[Sale] = relationship(back_populates="lines")


class SupplierOrder(Base):
    __tablename__ = "supplier_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier: Mapped[str] = mapped_column(String(255))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=16), default=OrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lines: Mapped[list[SupplierOrderLine]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class SupplierOrderLine(Base):
    __tablename__ = "supplier_order_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_orders.id", ondelete="CASCADE"), index=True
    )
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[SupplierOrder] = relationship(back_populates="lines")
    book: Mapped[Book] = relationship()


class CustomerRequest(Base):
    __tablename__ = "customer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name_enc: Mapped[str] = mapped_column(String(512))
    customer_contact_enc: Mapped[str] = mapped_column(String(512))
    book_title: Mapped[str] = mapped_column(String(255))
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, native_enum=False, length=16), default=RequestStatus.NEW
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now
    )
