from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api_server.deps import get_db, require_roles
from domain_services.enums import Role
from domain_services import sales
from domain_services.config import get_settings
from datetime import date

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/", dependencies=[Depends(require_roles(Role.OWNER, Role.MANAGER))])
def get_daily_totals(day: date = date.today(), db: Session = Depends(get_db)):
    settings = get_settings()
    return sales.daily_totals(db, day, settings.store_tz)

