from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api_server.deps import get_db, require_roles
from domain_services.enums import Role
from domain_services import backup

router = APIRouter(prefix="/backup", tags=["backup"])

@router.post("")
def run_backup(
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.OWNER)),
):
    return backup.run_backup(db)

