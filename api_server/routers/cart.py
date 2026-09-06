from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api_server.deps import get_db, get_cart_sid, require_user
from api_server.schemas import CartLineIn, CheckoutIn, QuantityIn
from domain_services import cart
from domain_services.config import get_settings
from domain_services.entities import User

router = APIRouter(prefix="/cart", tags=["cart"])

def get_active_cart(db: Session = Depends(get_db), sid: str = Depends(get_cart_sid)):
    return cart.get_or_create_cart(db, sid)

@router.post("/lines")
def add_line(data: CartLineIn, db: Session = Depends(get_db), c=Depends(get_active_cart)):
    try:
        cart.add_line(db, c, data.book_id, data.quantity)
        return {"message": "Added to cart"}
    except cart.InsufficientStock as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except cart.CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/lines/{book_id}")
def set_quantity(book_id: int, data: QuantityIn, db: Session = Depends(get_db), c=Depends(get_active_cart)):
    try:
        cart.set_quantity(db, c, book_id, data.quantity)
        return {"message": "Quantity updated"}
    except cart.InsufficientStock as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except cart.CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/lines/{book_id}")
def remove_line(book_id: int, db: Session = Depends(get_db), c=Depends(get_active_cart)):
    cart.remove_line(db, c, book_id)
    return {"message": "Removed from cart"}

@router.post("/checkout")
def checkout(data: CheckoutIn, db: Session = Depends(get_db), c=Depends(get_active_cart), user: User = Depends(require_user)):
    settings = get_settings()
    try:
        cart.checkout(db, c, payment_method=data.payment_method, tax_rate=settings.tax_rate, tender=data.tender, actor_id=user.id)
        return {"message": "Checkout successful"}
    except cart.EmptyCart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    except cart.InsufficientStock as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

