"""Cart service — a DB-backed basket keyed by the signed session id.

The cart survives across stateless (serverless) requests. Checkout is atomic:
availability is pre-checked, each line is decremented with an oversell-safe guard,
a single :class:`Sale` (with lines) is written, and the cart is cleared — all in
one transaction. If anything is short, no stock changes and no sale is created.
"""

from __future__ import annotations

from decimal import Decimal

from domain_services import inventory
from domain_services.checkout import quote_cart
from domain_services.entities import Book, Cart, CartLine, Sale, SaleLine
from domain_services.enums import PaymentMethod
from domain_services.money import Quote, line_total
from sqlalchemy import select
from sqlalchemy.orm import Session


class CartError(Exception):
    """Base class for cart errors."""


class EmptyCart(CartError):
    """Raised when checking out an empty cart."""


class InsufficientStock(CartError):
    """Raised when a requested quantity exceeds available stock."""


def get_or_create_cart(db: Session, session_id: str) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.session_id == session_id))
    if cart is None:
        cart = Cart(session_id=session_id)
        db.add(cart)
        db.flush()
    return cart


def _line_for(cart: Cart, book_id: int) -> CartLine | None:
    return next((line for line in cart.lines if line.book_id == book_id), None)


def _require_active_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None or not book.active:
        raise CartError(f"book {book_id} is not available")
    return book


def add_line(db: Session, cart: Cart, book_id: int, quantity: int) -> CartLine:
    """Add ``quantity`` of a book, merging with any existing line for that book."""
    if quantity <= 0:
        raise CartError("quantity must be positive")
    book = _require_active_book(db, book_id)
    existing = _line_for(cart, book_id)
    desired = quantity + (existing.quantity if existing else 0)
    if desired > book.quantity:
        raise InsufficientStock(
            f"only {book.quantity} of '{book.title}' in stock (requested {desired})"
        )
    if existing:
        existing.quantity = desired
        db.flush()
        return existing
    line = CartLine(cart_id=cart.id, book_id=book_id, quantity=quantity)
    cart.lines.append(line)
    db.flush()
    return line


def set_quantity(db: Session, cart: Cart, book_id: int, quantity: int) -> None:
    """Set an absolute quantity for a line; zero or less removes it."""
    line = _line_for(cart, book_id)
    if line is None:
        raise CartError(f"book {book_id} is not in the cart")
    if quantity <= 0:
        cart.lines.remove(line)
        db.flush()
        return
    book = _require_active_book(db, book_id)
    if quantity > book.quantity:
        raise InsufficientStock(
            f"only {book.quantity} of '{book.title}' in stock (requested {quantity})"
        )
    line.quantity = quantity
    db.flush()


def remove_line(db: Session, cart: Cart, book_id: int) -> None:
    line = _line_for(cart, book_id)
    if line is not None:
        cart.lines.remove(line)
        db.flush()


def totals(db: Session, cart: Cart, *, tax_rate: Decimal) -> Quote:
    """Live subtotal/tax/total for the current cart (no tender)."""
    price_lines = [(line.book.price, line.quantity) for line in cart.lines]
    if not price_lines:
        return Quote(subtotal=Decimal("0.00"), tax=Decimal("0.00"), total=Decimal("0.00"))
    return quote_cart(
        price_lines, payment_method=PaymentMethod.CARD, tax_rate=tax_rate
    )


def checkout(
    db: Session,
    cart: Cart,
    *,
    payment_method: PaymentMethod,
    tax_rate: Decimal,
    tender: Decimal | None = None,
    actor_id: int | None = None,
) -> Sale:
    """Commit the entire cart as one atomic sale."""
    lines = list(cart.lines)
    if not lines:
        raise EmptyCart("cannot check out an empty cart")

    price_lines = [(line.book.price, line.quantity) for line in lines]
    priced = quote_cart(
        price_lines, payment_method=payment_method, tax_rate=tax_rate, tender=tender
    )

    # Pre-check availability so a short line changes nothing.
    for line in lines:
        if not line.book.active or line.book.quantity < line.quantity:
            raise InsufficientStock(
                f"only {line.book.quantity} of '{line.book.title}' in stock"
            )

    # Atomic decrements (guards against concurrent oversell).
    for line in lines:
        if not inventory.try_decrement(db, line.book_id, line.quantity, actor_id=actor_id):
            raise InsufficientStock(f"'{line.book.title}' sold out during checkout")

    sale = Sale(
        payment_method=payment_method,
        subtotal=priced.subtotal,
        tax=priced.tax,
        total=priced.total,
        tender=tender if payment_method is PaymentMethod.CASH else None,
        change=priced.change,
        cashier_id=actor_id,
    )
    db.add(sale)
    db.flush()
    for line in lines:
        db.add(
            SaleLine(
                sale_id=sale.id,
                book_id=line.book_id,
                title=line.book.title,
                unit_price=line.book.price,
                quantity=line.quantity,
                line_total=line_total(line.book.price, line.quantity),
            )
        )
    cart.lines.clear()
    db.flush()
    return sale

