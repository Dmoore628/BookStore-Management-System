from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api_server.deps import get_db, require_roles, require_user
from domain_services.enums import Role
from api_server.schemas import OrderIn
from domain_services import orders
from domain_services.entities import User

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def list_orders(db: Session = Depends(get_db)):
    return orders.list_orders(db)

@router.post("/", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def create_order(data: OrderIn, db: Session = Depends(get_db)):
    try:
        lines = [(l.book_id, l.quantity) for l in data.lines]
        return orders.create_order(db, supplier=data.supplier, lines=lines)
    except orders.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/receive", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def receive_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        return orders.receive_order(db, order_id, actor_id=user.id)
    except orders.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))

