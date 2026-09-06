from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api_server.deps import get_db, require_roles
from domain_services.enums import Role
from api_server.schemas import BookIn, BookEdit, BookOut, ReceiveIn, CorrectIn
from domain_services import inventory
from api_server.deps import require_user
from domain_services.entities import User

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    return inventory.list_books(db)

@router.post("/", response_model=BookOut, dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def add_book(book: BookIn, db: Session = Depends(get_db), user: User = Depends(require_user)):
    return inventory.add_book(db, **book.model_dump(), actor_id=user.id)

@router.patch("/{book_id}", response_model=BookOut, dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def edit_book(book_id: int, book: BookEdit, db: Session = Depends(get_db)):
    updated = inventory.edit_book(db, book_id, **book.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated

@router.post("/{book_id}/receive", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def receive_stock(book_id: int, data: ReceiveIn, db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        inventory.receive_stock(db, book_id, data.quantity, actor_id=user.id, note=data.note)
        return {"message": "Stock received"}
    except inventory.BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found")

@router.post("/{book_id}/correct", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def correct_stock(book_id: int, data: CorrectIn, db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        inventory.correct_stock(db, book_id, data.quantity, actor_id=user.id, note=data.note)
        return {"message": "Stock corrected"}
    except inventory.BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found")

