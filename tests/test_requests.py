import pytest
from domain_services import requests
from domain_services.enums import RequestStatus
from domain_services.requests import RequestError
from sqlalchemy.orm import Session


def test_create_request_encrypts_pii(db: Session) -> None:
    request = requests.create_request(
        db, customer_name="Jane Doe", customer_contact="555-0100", book_title="Dune"
    )
    assert "Jane Doe" not in request.customer_name_enc
    assert "555-0100" not in request.customer_contact_enc
    revealed = requests.reveal(request)
    assert revealed.customer_name == "Jane Doe"
    assert revealed.customer_contact == "555-0100"


def test_status_transitions_new_to_fulfilled(db: Session) -> None:
    request = requests.create_request(
        db, customer_name="J", customer_contact="5", book_title="D"
    )
    requests.update_status(db, request.id, RequestStatus.ORDERED)
    requests.update_status(db, request.id, RequestStatus.FULFILLED)
    assert request.status is RequestStatus.FULFILLED


def test_invalid_transition_rejected(db: Session) -> None:
    request = requests.create_request(
        db, customer_name="J", customer_contact="5", book_title="D"
    )
    with pytest.raises(RequestError):
        requests.update_status(db, request.id, RequestStatus.FULFILLED)  # NEW -> FULFILLED


def test_missing_fields_rejected(db: Session) -> None:
    with pytest.raises(RequestError):
        requests.create_request(db, customer_name="", customer_contact="x", book_title="y")


def test_list_requests_filters_by_status(db: Session) -> None:
    requests.create_request(db, customer_name="A", customer_contact="1", book_title="X")
    assert len(requests.list_requests(db, status=RequestStatus.NEW)) == 1
    assert len(requests.list_requests(db, status=RequestStatus.FULFILLED)) == 0

