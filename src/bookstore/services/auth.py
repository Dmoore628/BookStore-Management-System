"""Authentication and role authorization."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import verify_password


class AuthorizationError(Exception):
    """Raised when a user lacks the required role."""


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Return the active user if credentials are valid, else None."""
    user = db.scalar(select(User).where(User.username == username, User.active.is_(True)))
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def has_role(user: User, *allowed: Role) -> bool:
    return user.role in allowed


def require_role(user: User, *allowed: Role) -> None:
    """Raise :class:`AuthorizationError` unless the user holds an allowed role."""
    if not has_role(user, *allowed):
        raise AuthorizationError(
            f"{user.username} ({user.role}) is not permitted; requires one of "
            f"{', '.join(r.value for r in allowed)}"
        )
