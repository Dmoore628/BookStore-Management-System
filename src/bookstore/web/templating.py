"""Jinja template environment and a render helper with shared context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from bookstore.config import get_settings
from bookstore.models.entities import User

_TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


def _money(value: Any) -> str:
    return f"{get_settings().currency} {value:,.2f}"


templates.env.filters["money"] = _money


def render(
    request: Request,
    template: str,
    context: dict[str, Any] | None = None,
    *,
    user: User | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Render ``template`` with common context (settings, current user) merged in."""
    settings = get_settings()
    merged: dict[str, Any] = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "current_user": user,
    }
    if context:
        merged.update(context)
    return templates.TemplateResponse(template, merged, status_code=status_code)
