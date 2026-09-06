"""Shared FastAPI dependencies: database session, current user, role guards.

Sessions are signed cookies (Starlette ``SessionMiddleware``), so no server-side
session store is needed — safe for stateless serverless hosting. A per-browser
cart id is stored in the same signed session.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from domain_services.database import get_db as _get_db
from domain_services.entities import User
from domain_services.enums import Role
from domain_services import auth

SESSION_USER_KEY = "user_id"
SESSION_CART_KEY = "cart_sid"


def get_db() -> Iterator[Session]:
    yield from _get_db()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Return the signed-in user, or None."""
    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        return None
    return db.get(User, int(user_id))


def require_user(user: User | None = Depends(get_current_user)) -> User:
    """Return the signed-in user or raise 401."""
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_roles(*roles: Role):  # type: ignore[no-untyped-def]
    """Build a dependency that requires one of ``roles``."""

    def _dep(user: User = Depends(require_user)) -> User:
        if not auth.has_role(user, *roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _dep


def get_cart_sid(request: Request) -> str:
    """Return (creating if needed) the per-browser cart session id."""
    sid = request.session.get(SESSION_CART_KEY)
    if not sid:
        sid = secrets.token_urlsafe(24)
        request.session[SESSION_CART_KEY] = sid
    return sid

