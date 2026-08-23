from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.stand_service import StandService


router = APIRouter()


@router.get("/")
def get_all_stands(
    db: Session = Depends(get_db),
):
    service = StandService(db)
    return service.get_all_stands()


@router.get("/{stand_id}")
def get_stand_details(
    stand_id: int,
    db: Session = Depends(get_db),
):
    service = StandService(db)
    return service.get_stand_details(stand_id)