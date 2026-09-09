import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin, require_operator
from app.database.session import get_db
from app.models.enums import LocationEnum, StatusEnum
from app.models.stand_asset import StandAsset
from app.models.stand_component import StandComponentPreparation, StandComponentPreparationItem, StandComponentType
from app.models.user import User
from app.services.stand_service import StandService

router = APIRouter()


class CreateStandSchema(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    initial_life_hours: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class ComponentItemInput(BaseModel):
    component_type_id: int
    new_qty: int = Field(default=0, ge=0)
    reused_qty: int = Field(default=0, ge=0)
    carried_life_hours: float | None = Field(default=None, ge=0)


class ComponentPreparationInput(BaseModel):
    items: list[ComponentItemInput] = []
    prepared_by: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)
    skip: bool = False


def _position_number(code: str) -> int | None:
    match = re.match(r"^0*(10|[1-9])", (code or "").strip())
    return int(match.group(1)) if match else None


def _component_payload(db: Session, stand: StandAsset):
    pos = _position_number(stand.code)
    types = db.query(StandComponentType).filter(StandComponentType.active.is_(True)).order_by(StandComponentType.id).all()
    applicable = [t for t in types if not t.even_position_extra or (pos is not None and pos % 2 == 0)]
    latest = db.query(StandComponentPreparation).filter(
        StandComponentPreparation.stand_id == stand.id,
        StandComponentPreparation.finalized_at.is_(None),
    ).order_by(StandComponentPreparation.created_at.desc()).first()
    item_map = {i.component_type_id: i for i in (latest.items if latest else [])}
    return {
        "stand_id": stand.id,
        "stand_code": stand.code,
        "position_number": pos,
        "state": latest.state if latest else "NOT_STARTED",
        "prepared_by": latest.prepared_by if latest else None,
        "notes": latest.notes if latest else None,
        "components": [
            {
                "component_type_id": t.id,
                "name": t.name,
                "required_qty": t.required_qty,
                "expected_life_hours": t.expected_life_hours,
                "criticality": t.criticality,
                "new_qty": item_map[t.id].new_qty if t.id in item_map else 0,
                "reused_qty": item_map[t.id].reused_qty if t.id in item_map else 0,
                "carried_life_hours": item_map[t.id].carried_life_hours if t.id in item_map else None,
                "is_extra": bool(t.even_position_extra),
            }
            for t in applicable
        ],
    }


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


@router.get("/{stand_id}/components")
def get_component_preparation(stand_id: int, db: Session = Depends(get_db)):
    stand = db.get(StandAsset, stand_id)
    if not stand:
        raise HTTPException(404, "Stand not found")
    return _component_payload(db, stand)


@router.post("/{stand_id}/components")
def save_component_preparation(
    stand_id: int,
    payload: ComponentPreparationInput,
    db: Session = Depends(get_db),
    _: User = Depends(require_operator),
):
    stand = db.get(StandAsset, stand_id)
    if not stand:
        raise HTTPException(404, "Stand not found")
    if stand.current_status != StatusEnum.PENDING:
        raise HTTPException(400, "Components can be prepared only while the stand is PENDING.")

    prepared_by = payload.prepared_by.strip()
    if not prepared_by:
        raise HTTPException(400, "Prepared by is required.")

    current = db.query(StandComponentPreparation).filter(
        StandComponentPreparation.stand_id == stand.id,
        StandComponentPreparation.finalized_at.is_(None),
    ).order_by(StandComponentPreparation.created_at.desc()).first()
    if not current:
        current = StandComponentPreparation(
            stand_id=stand.id,
            state="SKIPPED" if payload.skip else "SAVED",
            prepared_by=prepared_by,
            notes=(payload.notes or "").strip() or None,
            created_at=datetime.utcnow(),
        )
        db.add(current)
        db.flush()
    else:
        current.state = "SKIPPED" if payload.skip else "SAVED"
        current.prepared_by = prepared_by
        current.notes = (payload.notes or "").strip() or None
        current.items.clear()
        db.flush()

    if not payload.skip:
        types = {t.id: t for t in db.query(StandComponentType).filter(StandComponentType.active.is_(True)).all()}
        pos = _position_number(stand.code)
        for row in payload.items:
            component = types.get(row.component_type_id)
            if not component:
                raise HTTPException(400, f"Unknown component type {row.component_type_id}.")
            if component.even_position_extra and (pos is None or pos % 2 != 0):
                raise HTTPException(400, f"{component.name} applies only to even stand positions.")
            total = row.new_qty + row.reused_qty
            if component.required_qty is not None and total > component.required_qty:
                raise HTTPException(400, f"{component.name}: new + reused cannot exceed {component.required_qty}.")
            if total == 0 and row.carried_life_hours is None:
                continue
            db.add(StandComponentPreparationItem(
                preparation_id=current.id,
                component_type_id=component.id,
                new_qty=row.new_qty,
                reused_qty=row.reused_qty,
                carried_life_hours=row.carried_life_hours,
            ))

    db.commit()
    db.refresh(current)
    return _component_payload(db, stand)


@router.get("/{stand_id}")
def get_stand_details(stand_id: int, db: Session = Depends(get_db)):
    return StandService(db).get_stand_details(stand_id)
