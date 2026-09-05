"""Application factory and ASGI entrypoint.

Wires middleware, static assets, and routers; on startup it ensures the schema
exists (dev/demo convenience) and creates the initial owner account if the users
table is empty. Exposes ``app`` for ASGI servers (uvicorn / Vercel).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from bookstore.config import get_settings
from bookstore.database import Base, get_engine
from bookstore.models.entities import User
from bookstore.models.enums import Role
from bookstore.security import hash_password
from bookstore.api.routers import (
    auth as auth_router,
    books as books_router,
    cart as cart_router,
    sales as sales_router,
    orders as orders_router,
    requests as requests_router,
    backup as backup_router,
)
from bookstore.web.pages import router as web_router
from bookstore.web.templating import STATIC_DIR


def _ensure_schema_and_owner() -> None:
    settings = get_settings()
    engine = get_engine()
    if settings.auto_create_schema:
        Base.metadata.create_all(engine)
    if not settings.initial_owner_password:
        return
    with Session(engine) as db:
        user_count = db.scalar(select(func.count()).select_from(User))
        if user_count:
            return
        db.add(
            User(
                username=settings.initial_owner_username,
                password_hash=hash_password(settings.initial_owner_password),
                role=Role.OWNER,
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _ensure_schema_and_owner()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie_name,
        https_only=settings.session_https_only,
        max_age=settings.session_max_age_seconds,
        same_site="lax",
    )
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(web_router)
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(books_router.router, prefix="/api")
    app.include_router(cart_router.router, prefix="/api")
    app.include_router(sales_router.router, prefix="/api")
    app.include_router(orders_router.router, prefix="/api")
    app.include_router(requests_router.router, prefix="/api")
    app.include_router(backup_router.router, prefix="/api")

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
