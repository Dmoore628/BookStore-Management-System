"""Server-rendered pages and htmx endpoints for the staff console."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bookstore.api.deps import (
    SESSION_USER_KEY,
    get_cart_sid,
    get_current_user,
    get_db,
)
from bookstore.config import get_settings
from bookstore.models.entities import Book, CustomerRequest, SupplierOrder, User
from bookstore.models.enums import OrderStatus, PaymentMethod, RequestStatus, Role
from bookstore.services import auth, cart, inventory, orders, requests, sales
from bookstore.web.templating import render

router = APIRouter(tags=["web"])

_LOGIN = RedirectResponse("/login", status_code=303)


def _can_manage(user: User) -> bool:
    return auth.has_role(user, Role.OWNER, Role.MANAGER)


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User | None = Depends(get_current_user)) -> HTMLResponse:
    if user is not None:
        return RedirectResponse("/", status_code=303)  # type: ignore[return-value]
    return render(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = auth.authenticate(db, username, password)
    if user is None:
        return render(
            request,
            "login.html",
            {"error": "Invalid username or password.", "username": username},
            status_code=401,
        )
    request.session[SESSION_USER_KEY] = user.id
    return RedirectResponse("/", status_code=303)  # type: ignore[return-value]


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    settings = get_settings()
    today = datetime.now(ZoneInfo(settings.store_tz)).date()
    totals = sales.daily_totals(db, today, settings.store_tz)
    active_titles = db.scalar(select(func.count()).select_from(Book).where(Book.active.is_(True)))
    low_stock = db.scalar(
        select(func.count())
        .select_from(Book)
        .where(Book.active.is_(True), Book.quantity <= settings.low_stock_threshold)
    )
    open_orders = db.scalar(
        select(func.count())
        .select_from(SupplierOrder)
        .where(SupplierOrder.status == OrderStatus.PENDING)
    )
    open_requests = db.scalar(
        select(func.count())
        .select_from(CustomerRequest)
        .where(CustomerRequest.status.in_([RequestStatus.NEW, RequestStatus.ORDERED]))
    )
    return render(
        request,
        "home.html",
        {
            "today": today,
            "totals": totals,
            "active_titles": active_titles or 0,
            "low_stock": low_stock or 0,
            "open_orders": open_orders or 0,
            "open_requests": open_requests or 0,
        },
        user=user,
    )


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #
@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(
    request: Request,
    q: str = Query(default=""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    books = inventory.search(db, q) if q else inventory.list_books(db)
    ctx = {"books": books, "q": q, "can_manage": _can_manage(user),
           "threshold": get_settings().low_stock_threshold}
    template = "partials/_inventory_rows.html" if request.headers.get("HX-Request") else "inventory.html"
    return render(request, template, ctx, user=user)


@router.post("/inventory")
def inventory_add(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    price: str = Form(...),
    quantity: int = Form(0),
    shelf_location: str = Form(""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    if not _can_manage(user):
        return RedirectResponse("/inventory", status_code=303)
    try:
        inventory.add_book(
            db,
            title=title,
            author=author,
            isbn=isbn,
            price=Decimal(price),
            quantity=quantity,
            shelf_location=shelf_location,
            actor_id=user.id,
        )
        db.commit()
    except (inventory.InventoryError, InvalidOperation):
        db.rollback()
    return RedirectResponse("/inventory", status_code=303)


@router.post("/inventory/{book_id}/receive")
def inventory_receive(
    book_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    if _can_manage(user):
        try:
            inventory.receive_stock(db, book_id, quantity, actor_id=user.id)
            db.commit()
        except inventory.InventoryError:
            db.rollback()
    return RedirectResponse("/inventory", status_code=303)


@router.post("/inventory/{book_id}/correct")
def inventory_correct(
    book_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    if _can_manage(user):
        try:
            inventory.correct_stock(db, book_id, quantity, actor_id=user.id)
            db.commit()
        except inventory.InventoryError:
            db.rollback()
    return RedirectResponse("/inventory", status_code=303)


# --------------------------------------------------------------------------- #
# Point of Sale (cart)
# --------------------------------------------------------------------------- #
def _cart_context(request: Request, db: Session) -> dict:
    settings = get_settings()
    sid = get_cart_sid(request)
    current = cart.get_or_create_cart(db, sid)
    totals = cart.totals(db, current, tax_rate=settings.tax_rate)
    return {"cart": current, "totals": totals, "tax_rate_pct": settings.tax_rate * 100}


@router.get("/pos", response_class=HTMLResponse)
def pos_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    ctx = {"results": inventory.list_books(db)[:8], "q": ""}
    ctx.update(_cart_context(request, db))
    return render(request, "pos.html", ctx, user=user)


@router.get("/pos/search", response_class=HTMLResponse)
def pos_search(
    request: Request,
    q: str = Query(default=""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    results = inventory.search(db, q) if q else inventory.list_books(db)[:8]
    return render(request, "partials/_search_results.html", {"results": results, "q": q}, user=user)


def _cart_partial(request: Request, db: Session, user: User, error: str = "") -> HTMLResponse:
    ctx = _cart_context(request, db)
    ctx["error"] = error
    return render(request, "partials/_cart.html", ctx, user=user)


@router.post("/pos/cart/add", response_class=HTMLResponse)
def cart_add(
    request: Request,
    book_id: int = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    current = cart.get_or_create_cart(db, get_cart_sid(request))
    error = ""
    try:
        cart.add_line(db, current, book_id, quantity)
        db.commit()
    except cart.CartError as exc:
        db.rollback()
        error = str(exc)
    return _cart_partial(request, db, user, error)


@router.post("/pos/cart/update", response_class=HTMLResponse)
def cart_update(
    request: Request,
    book_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    current = cart.get_or_create_cart(db, get_cart_sid(request))
    error = ""
    try:
        cart.set_quantity(db, current, book_id, quantity)
        db.commit()
    except cart.CartError as exc:
        db.rollback()
        error = str(exc)
    return _cart_partial(request, db, user, error)


@router.post("/pos/cart/remove", response_class=HTMLResponse)
def cart_remove(
    request: Request,
    book_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    current = cart.get_or_create_cart(db, get_cart_sid(request))
    cart.remove_line(db, current, book_id)
    db.commit()
    return _cart_partial(request, db, user)


@router.post("/pos/checkout", response_class=HTMLResponse)
def pos_checkout(
    request: Request,
    payment_method: str = Form(...),
    tender: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    settings = get_settings()
    current = cart.get_or_create_cart(db, get_cart_sid(request))
    method = PaymentMethod.CASH if payment_method == "cash" else PaymentMethod.CARD
    tender_val: Decimal | None = None
    if method is PaymentMethod.CASH and tender.strip():
        try:
            tender_val = Decimal(tender)
        except InvalidOperation:
            return _cart_partial(request, db, user, "Enter a valid cash amount.")
    try:
        sale = cart.checkout(
            db, current, payment_method=method, tax_rate=settings.tax_rate, tender=tender_val,
            actor_id=user.id,
        )
        db.commit()
    except (cart.CartError, Exception) as exc:  # noqa: BLE001 - surfaced to cashier
        db.rollback()
        return _cart_partial(request, db, user, str(exc))
    return render(request, "partials/_receipt.html", {"sale": sale}, user=user)


# --------------------------------------------------------------------------- #
# Daily sales (manager/owner)
# --------------------------------------------------------------------------- #
@router.get("/sales", response_class=HTMLResponse)
def sales_page(
    request: Request,
    day: str = Query(default=""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    if not _can_manage(user):
        return RedirectResponse("/", status_code=303)  # type: ignore[return-value]
    settings = get_settings()
    try:
        selected = date.fromisoformat(day) if day else datetime.now(ZoneInfo(settings.store_tz)).date()
    except ValueError:
        selected = datetime.now(ZoneInfo(settings.store_tz)).date()
    totals = sales.daily_totals(db, selected, settings.store_tz)
    rows = sales.list_sales(db, selected, settings.store_tz)
    return render(
        request, "sales.html", {"day": selected, "totals": totals, "sales": rows}, user=user
    )


# --------------------------------------------------------------------------- #
# Supplier orders (manager/owner)
# --------------------------------------------------------------------------- #
@router.get("/orders", response_class=HTMLResponse)
def orders_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    if not _can_manage(user):
        return RedirectResponse("/", status_code=303)  # type: ignore[return-value]
    return render(
        request,
        "orders.html",
        {"orders": orders.list_orders(db), "books": inventory.list_books(db)},
        user=user,
    )


@router.post("/orders")
def orders_create(
    request: Request,
    supplier: str = Form(...),
    book_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    if _can_manage(user):
        try:
            orders.create_order(db, supplier=supplier, lines=[(book_id, quantity)])
            db.commit()
        except orders.OrderError:
            db.rollback()
    return RedirectResponse("/orders", status_code=303)


@router.post("/orders/{order_id}/receive")
def orders_receive(
    order_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    if _can_manage(user):
        try:
            orders.receive_order(db, order_id, actor_id=user.id)
            db.commit()
        except orders.OrderError:
            db.rollback()
    return RedirectResponse("/orders", status_code=303)


# --------------------------------------------------------------------------- #
# Customer requests
# --------------------------------------------------------------------------- #
@router.get("/requests", response_class=HTMLResponse)
def requests_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    if user is None:
        return _LOGIN  # type: ignore[return-value]
    rows = [requests.reveal(r) for r in requests.list_requests(db)]
    return render(request, "requests.html", {"requests": rows}, user=user)


@router.post("/requests")
def requests_create(
    request: Request,
    customer_name: str = Form(...),
    customer_contact: str = Form(...),
    book_title: str = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    try:
        requests.create_request(
            db, customer_name=customer_name, customer_contact=customer_contact,
            book_title=book_title,
        )
        db.commit()
    except requests.RequestError:
        db.rollback()
    return RedirectResponse("/requests", status_code=303)


@router.post("/requests/{request_id}/status")
def requests_status(
    request_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    if user is None:
        return _LOGIN
    try:
        requests.update_status(db, request_id, RequestStatus(status))
        db.commit()
    except (requests.RequestError, ValueError):
        db.rollback()
    return RedirectResponse("/requests", status_code=303)
