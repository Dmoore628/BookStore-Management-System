from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from bookstore.schemas import LoginIn
from bookstore.services import auth
from bookstore.api.deps import SESSION_USER_KEY, require_user, get_db
from bookstore.models.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(credentials: LoginIn, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    user = auth.authenticate(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    request.session[SESSION_USER_KEY] = str(user.id)
    return {"message": "Logged in"}

@router.post("/logout")
def logout(request: Request, user: User = Depends(require_user)) -> dict[str, str]:
    request.session.pop(SESSION_USER_KEY, None)
    return {"message": "Logged out"}
