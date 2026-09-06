from collections.abc import Callable
from pathlib import Path

from domain_services import backup
from domain_services.entities import Book
from sqlalchemy.orm import Session


def test_backup_writes_to_file_destination(
    db: Session, make_book: Callable[..., Book], tmp_path: Path
) -> None:
    make_book()
    result = backup.run_backup(db, destination=f"file://{tmp_path.as_posix()}")
    assert Path(result.location).exists()
    assert result.table_count == 10
    assert result.row_count >= 1


def test_payload_contains_all_tables(db: Session) -> None:
    payload = backup.build_backup_payload(db)
    assert {
        "users",
        "books",
        "stock_movements",
        "carts",
        "cart_lines",
        "sales",
        "sale_lines",
        "supplier_orders",
        "supplier_order_lines",
        "customer_requests",
    } == set(payload)

