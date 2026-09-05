from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from bookstore.api.deps import get_db, require_roles
from bookstore.models.enums import Role
from bookstore.schemas import RequestIn, RequestStatusIn
from bookstore.services import requests

router = APIRouter(prefix="/requests", tags=["requests"])

@router.get("/", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def list_requests(db: Session = Depends(get_db)):
    raw = requests.list_requests(db)
    return [requests.reveal(r) for r in raw]

@router.post("/", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER, Role.CASHIER))])
def create_request(data: RequestIn, db: Session = Depends(get_db)):
    try:
        return requests.create_request(db, customer_name=data.customer_name, customer_contact=data.customer_contact, book_title=data.book_title)
    except requests.RequestError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{request_id}/status", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def update_status(request_id: int, data: RequestStatusIn, db: Session = Depends(get_db)):
    try:
        return requests.update_status(db, request_id, data.status)
    except requests.RequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
