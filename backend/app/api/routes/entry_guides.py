from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entry_guide_asset import EntryGuideAsset
from app.models.enums import EntryGuideConditionEnum, LocationEnum, StatusEnum
from app.services.entry_guide_service import EntryGuideService
from app.schemas.entry_guide import InstallEntryGuideSchema, RemoveEntryGuideSchema, UpdateEntryGuideConditionSchema

router = APIRouter()


class CreateEntryGuideSchema(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    condition: EntryGuideConditionEnum = EntryGuideConditionEnum.OLD
    notes: str | None = Field(default=None, max_length=500)


class ReadyEntryGuideSchema(BaseModel):
    guide_code: str
    updated_by: str = Field(min_length=1, max_length=100)


@router.get("/")
def list_guides(db: Session = Depends(get_db)):
    guides = db.query(EntryGuideAsset).order_by(EntryGuideAsset.code).all()
    return [{
        "id": g.id, "code": g.code, "condition": g.condition,
        "current_status": g.current_status, "current_location": g.current_location,
        "current_position_id": g.current_position_id, "lifetime_hours": g.lifetime_hours,
        "condition_notes": g.condition_notes,
    } for g in guides]


@router.post("/", status_code=201)
def create_guide(payload: CreateEntryGuideSchema, db: Session = Depends(get_db)):
    code = payload.code.strip()
    if db.query(EntryGuideAsset).filter(EntryGuideAsset.code == code).first():
        raise HTTPException(status_code=409, detail="Entry guide already exists")
    guide = EntryGuideAsset(
        code=code,
        condition=payload.condition,
        condition_notes=payload.notes,
        current_location=LocationEnum.READY_AREA,
        current_status=StatusEnum.READY,
    )
    db.add(guide); db.commit(); db.refresh(guide)
    return {"id": guide.id, "code": guide.code, "condition": guide.condition, "current_status": guide.current_status}


@router.post("/ready")
def mark_guide_ready(payload: ReadyEntryGuideSchema, db: Session = Depends(get_db)):
    guide = db.query(EntryGuideAsset).filter(EntryGuideAsset.code == payload.guide_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Entry guide not found")
    if guide.current_status == StatusEnum.INSTALLED:
        raise HTTPException(status_code=400, detail="Running entry guide cannot be marked Ready")
    guide.current_status = StatusEnum.READY
    guide.current_location = LocationEnum.READY_AREA
    db.commit()
    return {"status": "success", "guide_code": guide.code, "updated_by": payload.updated_by}


@router.post("/install")
def install_guide(payload: InstallEntryGuideSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).install_guide(payload.guide_code, payload.position_id, None, payload.operator_name)


@router.post("/remove")
def remove_guide(payload: RemoveEntryGuideSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).remove_guide(payload.guide_code, payload.removed_by, payload.removal_reason, None)


@router.post("/condition")
def update_guide_condition(payload: UpdateEntryGuideConditionSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).update_condition(payload.guide_code, payload.condition, payload.notes, None)
