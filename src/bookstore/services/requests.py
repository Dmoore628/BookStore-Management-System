"""Customer special-order requests.

Only the minimum PII is collected (name + contact), and it is encrypted at rest.
Status follows NEW → ORDERED → FULFILLED, with CANCELLED reachable from any
non-terminal state.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from bookstore.models.entities import CustomerRequest
from bookstore.models.enums import RequestStatus
from bookstore.security import decrypt, encrypt

_ALLOWED: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.NEW: {RequestStatus.ORDERED, RequestStatus.CANCELLED},
    RequestStatus.ORDERED: {RequestStatus.FULFILLED, RequestStatus.CANCELLED},
    RequestStatus.FULFILLED: set(),
    RequestStatus.CANCELLED: set(),
}


class RequestError(Exception):
    """Raised on invalid customer-request operations."""


@dataclass(frozen=True)
class DecryptedRequest:
    id: int
    customer_name: str
    customer_contact: str
    book_title: str
    status: RequestStatus


def create_request(
    db: Session, *, customer_name: str, customer_contact: str, book_title: str
) -> CustomerRequest:
    """Create a request, encrypting the customer's PII."""
    if not customer_name or not customer_contact or not book_title:
        raise RequestError("name, contact, and book title are required")
    request = CustomerRequest(
        customer_name_enc=encrypt(customer_name),
        customer_contact_enc=encrypt(customer_contact),
        book_title=book_title,
        status=RequestStatus.NEW,
    )
    db.add(request)
    db.flush()
    return request


def reveal(request: CustomerRequest) -> DecryptedRequest:
    """Decrypt a request's PII for an authorized viewer."""
    return DecryptedRequest(
        id=request.id,
        customer_name=decrypt(request.customer_name_enc),
        customer_contact=decrypt(request.customer_contact_enc),
        book_title=request.book_title,
        status=request.status,
    )


def list_requests(
    db: Session, *, status: RequestStatus | None = None
) -> Sequence[CustomerRequest]:
    stmt = select(CustomerRequest).order_by(CustomerRequest.created_at.desc())
    if status is not None:
        stmt = stmt.where(CustomerRequest.status == status)
    return db.scalars(stmt).all()


def update_status(
    db: Session, request_id: int, new_status: RequestStatus
) -> CustomerRequest:
    """Advance a request's status, enforcing the allowed transitions."""
    request = db.get(CustomerRequest, request_id)
    if request is None:
        raise RequestError(f"request {request_id} does not exist")
    if new_status not in _ALLOWED[request.status]:
        raise RequestError(f"cannot move request from {request.status} to {new_status}")
    request.status = new_status
    db.flush()
    return request
