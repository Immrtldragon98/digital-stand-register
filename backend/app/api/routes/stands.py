from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.enums import LocationEnum, StatusEnum
from app.models.stand_asset import StandAsset
from app.models.user import User
from app.services.stand_service import StandService

router = APIRouter()


class CreateStandSchema(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    initial_life_hours: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


@router.get("/")
def get_all_stands(db: Session = Depends(get_db)):
    return StandService(db).get_all_stands()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_stand(payload: CreateStandSchema, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    code = payload.code.strip().upper()
    if db.query(StandAsset).filter(StandAsset.code == code).first():
        raise HTTPException(409, "Stand already exists")
    stand = StandAsset(
        code=code,
        current_location=LocationEnum.WIP,
        current_status=StatusEnum.YET_TO_READY,
        lifetime_hours=payload.initial_life_hours,
        condition_notes=(payload.notes or "").strip() or None,
    )
    db.add(stand)
    db.commit()
    db.refresh(stand)
    return {
        "id": stand.id,
        "code": stand.code,
        "current_status": stand.current_status,
        "current_location": stand.current_location,
        "lifetime_hours": stand.lifetime_hours,
    }


@router.get("/{stand_id}")
def get_stand_details(stand_id: int, db: Session = Depends(get_db)):
    return StandService(db).get_stand_details(stand_id)
