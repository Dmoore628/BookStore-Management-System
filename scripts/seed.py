"""Load a realistic independent-bookstore catalog after the owner account exists."""

import os

from bookstore.config import get_settings
from bookstore.database import Base, SessionLocal, engine
from bookstore.services.auth import bootstrap_owner, create_staff
from bookstore.services.inventory import InventoryError, create_book


TITLES = [
    ("The Night Watch", "Sarah Waters", "9781594480508", "16.00", 5, "F2-FIC"),
    ("Beloved", "Toni Morrison", "9781400033416", "17.00", 4, "A1-LIT"),
    ("Piranesi", "Susanna Clarke", "9781635577808", "18.00", 6, "F1-FIC"),
    ("Klara and the Sun", "Kazuo Ishiguro", "9780593311295", "16.95", 3, "F3-FIC"),
    ("The Left Hand of Darkness", "Ursula K. Le Guin", "9780441478125", "15.00", 2, "S1-SF"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        bootstrap_owner(session)
        for username, password, display, role in (
            ("richard", os.environ.get("SEED_MANAGER_PASSWORD", "ChangeMeRichard1"), "Richard Hale", "manager"),
            ("stephen", os.environ.get("SEED_CASHIER_PASSWORD", "ChangeMeStephen1"), "Stephen Park", "cashier"),
        ):
            try:
                create_staff(
                    session,
                    username=username,
                    password=password,
                    display_name=display,
                    role=role,
                )
            except ValueError:
                continue
        for title, author, isbn, price, qty, shelf in TITLES:
            try:
                create_book(
                    session,
                    title=title,
                    author=author,
                    isbn=isbn,
                    price=price,
                    quantity=qty,
                    shelf_location=shelf,
                )
            except InventoryError:
                continue
        session.commit()
    settings = get_settings()
    print(f"Seed complete for {settings.app_name} ({settings.environment}).")


if __name__ == "__main__":
    main()
