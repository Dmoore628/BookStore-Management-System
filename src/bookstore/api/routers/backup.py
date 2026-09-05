from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from bookstore.api.deps import get_db, require_roles
from bookstore.models.enums import Role
from bookstore.services import backup

router = APIRouter(prefix="/backup", tags=["backup"])

@router.post("")
def run_backup(
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.OWNER)),
):
    return backup.run_backup(db)
