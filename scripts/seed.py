"""Seed the database with staff accounts and realistic demo inventory.

Idempotent: safe to run repeatedly. Reads all credentials from settings/env —
no passwords are hardcoded. Run with:  python -m scripts.seed
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain_services.config import get_settings
from domain_services.database import Base, get_engine
from domain_services.entities import Sale, User
from domain_services.enums import PaymentMethod, Role
from domain_services.security import hash_password
from domain_services import cart, inventory

DEMO_BOOKS = [
    ("The Pragmatic Programmer", "Hunt & Thomas", "9780135957059", "49.99", 12, "A1"),
    ("Clean Code", "Robert C. Martin", "9780132350884", "44.50", 8, "A2"),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "9781449373320", "59.99", 5, "A3"),
    ("Domain-Driven Design", "Eric Evans", "9780321125217", "54.95", 3, "B1"),
    ("Refactoring", "Martin Fowler", "9780134757599", "47.99", 2, "B2"),
    ("The Mythical Man-Month", "Frederick Brooks", "9780201835953", "39.99", 6, "B3"),
    ("Introduction to Algorithms", "Cormen et al.", "9780262046305", "89.99", 4, "C1"),
    ("SICP", "Abelson & Sussman", "9780262510875", "72.00", 3, "C2"),
    ("Compilers (The Dragon Book)", "Aho et al.", "9780321486813", "84.99", 2, "C3"),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", "24.99", 15, "D1"),
    ("Educated", "Tara Westover", "9780399590504", "18.00", 9, "D2"),
    ("The Midnight Library", "Matt Haig", "9780525559474", "16.99", 11, "D3"),
]


def _ensure_user(db: Session, username: str | None, password: str | None, role: Role) -> None:
    if not username or not password:
        return
    if db.scalar(select(User).where(User.username == username)):
        return
    db.add(User(username=username, password_hash=hash_password(password), role=role))


def seed(db: Session) -> None:
    settings = get_settings()
    _ensure_user(db, settings.initial_owner_username, settings.initial_owner_password, Role.OWNER)
    _ensure_user(db, settings.seed_manager_username, settings.seed_manager_password, Role.MANAGER)
    _ensure_user(db, settings.seed_cashier_username, settings.seed_cashier_password, Role.CASHIER)
    db.flush()

    existing = {b.isbn for b in inventory.list_books(db, include_inactive=True)}
    for title, author, isbn, price, qty, shelf in DEMO_BOOKS:
        if isbn in existing:
            continue
        inventory.add_book(
            db,
            title=title,
            author=author,
            isbn=isbn,
            price=Decimal(price),
            quantity=qty,
            shelf_location=shelf,
        )

    # One completed sale so the dashboard and sales log are non-empty on first view.
    if db.scalar(select(func.count()).select_from(Sale)) == 0:
        books = list(inventory.list_books(db))
        if books:
            demo_cart = cart.get_or_create_cart(db, "seed-demo-cart")
            cart.add_line(db, demo_cart, books[0].id, 1)
            cart.add_line(db, demo_cart, books[-1].id, 2)
            cart.checkout(
                db, demo_cart, payment_method=PaymentMethod.CARD, tax_rate=settings.tax_rate
            )
    db.commit()


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed(db)
    print("Seed complete.")


if __name__ == "__main__":
    main()

