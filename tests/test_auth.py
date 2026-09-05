import pytest
from sqlalchemy.orm import Session

from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import hash_password
from bookstore.services import auth
from bookstore.services.auth import AuthorizationError


def test_authenticate_valid(db: Session, owner: User) -> None:
    result = auth.authenticate(db, "damian", "owner-pass")
    assert result is not None
    assert result.id == owner.id


def test_authenticate_bad_password(db: Session, owner: User) -> None:
    assert auth.authenticate(db, "damian", "wrong") is None


def test_authenticate_unknown_user(db: Session) -> None:
    assert auth.authenticate(db, "ghost", "x") is None


def test_inactive_user_cannot_authenticate(db: Session) -> None:
    user = User(
        username="ex", password_hash=hash_password("p"), role=Role.CASHIER, active=False
    )
    db.add(user)
    db.flush()
    assert auth.authenticate(db, "ex", "p") is None


def test_require_role_allows(db: Session, owner: User) -> None:
    auth.require_role(owner, Role.OWNER, Role.MANAGER)  # should not raise


def test_require_role_denies(db: Session) -> None:
    cashier = User(username="c", password_hash=hash_password("p"), role=Role.CASHIER)
    db.add(cashier)
    db.flush()
    with pytest.raises(AuthorizationError):
        auth.require_role(cashier, Role.OWNER)
