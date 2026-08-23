from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.entry_guide_service import EntryGuideService
from app.schemas.entry_guide import (
    InstallEntryGuideSchema,
    RemoveEntryGuideSchema,
    UpdateEntryGuideConditionSchema,
)

router = APIRouter()


@router.post("/install")
def install_guide(payload: InstallEntryGuideSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).install_guide(payload.guide_code, payload.position_id, None, payload.operator_name)


@router.post("/remove")
def remove_guide(payload: RemoveEntryGuideSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).remove_guide(payload.guide_code, payload.removed_by, payload.removal_reason, None)


@router.post("/condition")
def update_guide_condition(payload: UpdateEntryGuideConditionSchema, db: Session = Depends(get_db)):
    return EntryGuideService(db).update_condition(payload.guide_code, payload.condition, payload.notes, None)
