import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Literal
from app.models.component_asset import ComponentAsset, ComponentFitting, PreparationAssetSelection
from app.models.inventory_item import InventoryItem
from app.models.activity_log import ActivityLog
from app.services.component_lifecycle_service import ComponentLifecycleService

from app.auth.dependencies import require_admin, require_operator
from app.database.session import get_db
from app.models.enums import LocationEnum, StatusEnum
from app.models.stand_asset import StandAsset
from app.models.stand_component import StandComponentPreparation, StandComponentPreparationItem, StandComponentType
from app.models.stand_event import StandCampaignEvent
from app.models.stand_installation import StandInstallation
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
    asset_ids: list[int] = Field(default_factory=list, max_length=100)


class ComponentPreparationInput(BaseModel):
    items: list[ComponentItemInput] = Field(default_factory=list, max_length=100)
    prepared_by: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)
    skip: bool = False


class RunningConditionInput(BaseModel):
    leakage: bool | None = None
    vibration: bool | None = None
    abnormal_sound: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


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
    selections = db.query(PreparationAssetSelection).filter_by(preparation_id=latest.id).all() if latest else []
    lifecycle = ComponentLifecycleService(db)
    assets = db.query(ComponentAsset).order_by(ComponentAsset.code).all()
    asset_payloads = [lifecycle.asset_payload(asset, stand.id) for asset in assets]
    inventories = {item.id: item for item in db.query(InventoryItem).all()}
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
                "inventory_item_id": t.inventory_item_id,
                "stock_quantity": inventories[t.inventory_item_id].quantity if t.inventory_item_id in inventories else None,
                "asset_ids": [selection.asset_id for selection in selections if selection.component_type_id == t.id],
                "available_assets": [asset for asset in asset_payloads if asset['component_type_id'] == t.id and asset['available']],
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
        current_status=StatusEnum.PENDING,
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


@router.patch("/{stand_id}/condition")
def update_running_condition(
    stand_id: int,
    payload: RunningConditionInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    stand = db.get(StandAsset, stand_id)
    if not stand:
        raise HTTPException(404, "Stand not found")
    active = db.query(StandInstallation).filter(
        StandInstallation.stand_id == stand.id,
        StandInstallation.removed_at.is_(None),
    ).first()
    if not active:
        raise HTTPException(400, "Condition flags can be updated only while the stand is running.")

    changes = []
    for field, label in (("leakage", "Leakage"), ("vibration", "Vibration"), ("abnormal_sound", "Abnormal sound")):
        value = getattr(payload, field)
        if value is None:
            continue
        old = bool(getattr(stand, field))
        if old == value:
            continue
        setattr(stand, field, value)
        changes.append((label, value))
        db.add(StandCampaignEvent(
            stand_id=stand.id,
            installation_id=active.id,
            category="OBSERVATION",
            event_type=f"{label} {'observed' if value else 'cleared'}",
            severity="MEDIUM" if value else "LOW",
            description=(payload.notes or "").strip() or None,
            action_taken="Condition flag updated from running stand view",
            recorded_by=user.username,
            event_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        ))

    if payload.notes is not None:
        stand.condition_notes = payload.notes.strip() or None
    db.commit()
    return {
        "stand_id": stand.id,
        "leakage": stand.leakage,
        "vibration": stand.vibration,
        "abnormal_sound": stand.abnormal_sound,
        "condition_notes": stand.condition_notes,
        "changes": [{"condition": label, "active": value} for label, value in changes],
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
    stand = db.query(StandAsset).filter_by(id=stand_id).with_for_update().first()
    if not stand:
        raise HTTPException(404, "Stand not found")
    if stand.current_status != StatusEnum.PENDING:
        raise HTTPException(400, "Components can be prepared only while the stand is PENDING.")

    if payload.skip and not (payload.notes or '').strip():
        raise HTTPException(400, 'Skipping tracking requires a reason.')
    if len({row.component_type_id for row in payload.items}) != len(payload.items):
        raise HTTPException(400, 'Duplicate component type in preparation.')
    if any(row.carried_life_hours is not None for row in payload.items):
        raise HTTPException(400, 'Pooled carried life is not supported. Register prior life on each component identity as admin.')
    all_ids = [asset_id for row in payload.items for asset_id in row.asset_ids]
    if len(set(all_ids)) != len(all_ids):
        raise HTTPException(400, 'A component identity cannot be selected more than once.')
    if not payload.skip:
        for row in payload.items:
            if len(row.asset_ids) != row.new_qty + row.reused_qty:
                raise HTTPException(400, 'Select one identity for every new and reused component.')
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
        db.query(PreparationAssetSelection).filter_by(preparation_id=current.id).delete()
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
            if total == 0:
                continue
            db.add(StandComponentPreparationItem(
                preparation_id=current.id,
                component_type_id=component.id,
                new_qty=row.new_qty,
                reused_qty=row.reused_qty,
                carried_life_hours=row.carried_life_hours,
            ))
            selected = db.query(ComponentAsset).filter(ComponentAsset.id.in_(row.asset_ids)).all()
            if len(selected) != len(row.asset_ids) or any(asset.component_type_id != component.id for asset in selected):
                raise HTTPException(400, 'Selected asset type does not match preparation.')
            if sum(asset.condition == 'NEW' for asset in selected) != row.new_qty:
                raise HTTPException(400, 'New component count must match selected identities.')
            for asset in selected:
                db.add(PreparationAssetSelection(preparation_id=current.id, component_type_id=component.id, asset_id=asset.id))

    db.commit()
    db.refresh(current)
    return _component_payload(db, stand)


class ComponentAssetInput(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    component_type_id: int
    condition: Literal['NEW', 'REUSED']
    prior_life_hours: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class ComponentInventoryInput(BaseModel):
    inventory_item_id: int


@router.get('/component-types')
def component_types(db: Session = Depends(get_db)):
    stock = {item.id: item for item in db.query(InventoryItem).all()}
    return [{'id':t.id,'name':t.name,'required_qty':t.required_qty,'inventory_item_id':t.inventory_item_id,
        'stock_quantity':stock[t.inventory_item_id].quantity if t.inventory_item_id in stock else None}
        for t in db.query(StandComponentType).filter_by(active=True).order_by(StandComponentType.id).all()]


@router.patch('/component-types/{component_type_id}/inventory')
def map_component_inventory(component_type_id:int, payload:ComponentInventoryInput, db:Session=Depends(get_db), user:User=Depends(require_admin)):
    component = db.query(StandComponentType).filter_by(id=component_type_id).with_for_update().first()
    item = db.get(InventoryItem,payload.inventory_item_id)
    if not component or not item or not item.is_active:
        raise HTTPException(404, 'Component type or active inventory item not found.')
    old = component.inventory_item_id
    component.inventory_item_id = item.id
    db.add(ActivityLog(user_id=user.id,action='MAP_COMPONENT_STOCK',timestamp=datetime.utcnow(),details=f'Component type {component.id}: inventory {old} -> {item.id}'))
    db.commit()
    return {'component_type_id':component.id,'inventory_item_id':item.id}


@router.get('/component-assets')
def list_component_assets(component_type_id:int|None=None, db:Session=Depends(get_db)):
    query = db.query(ComponentAsset)
    if component_type_id is not None:
        query = query.filter_by(component_type_id=component_type_id)
    service = ComponentLifecycleService(db)
    return [service.asset_payload(asset) for asset in query.order_by(ComponentAsset.code).limit(2000).all()]


@router.post('/component-assets',status_code=201)
def create_component_asset(payload:ComponentAssetInput, db:Session=Depends(get_db), user:User=Depends(require_admin)):
    component = db.get(StandComponentType,payload.component_type_id)
    if not component or not component.active:
        raise HTTPException(404, 'Active component type not found.')
    code = payload.code.strip().upper()
    if not code:
        raise HTTPException(400, 'Component identity is required.')
    if payload.condition == 'NEW' and payload.prior_life_hours not in (None,0):
        raise HTTPException(400, 'New components cannot have prior service life.')
    asset = ComponentAsset(code=code,component_type_id=component.id,condition=payload.condition,
        prior_life_hours=0 if payload.condition=='NEW' else payload.prior_life_hours,created_at=datetime.utcnow())
    db.add(asset)
    try:
        db.flush()
        db.add(ActivityLog(user_id=user.id,action='REGISTER_COMPONENT',timestamp=datetime.utcnow(),details=f'Component {asset.code} registered ({asset.condition}); prior life {asset.prior_life_hours}'))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, 'Component identity already exists.') from exc
    return ComponentLifecycleService(db).asset_payload(asset)


@router.get("/{stand_id}")
def get_stand_details(stand_id: int, db: Session = Depends(get_db)):
    return StandService(db).get_stand_details(stand_id)
