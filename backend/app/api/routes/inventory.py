from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin, require_operator
from app.database.session import get_db
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryOut,
    InventoryQuantityChange,
    InventorySetQuantity,
    InventoryTransactionOut,
    InventoryUpdate,
)

router = APIRouter()


def _get_item(db: Session, item_id: int) -> InventoryItem:
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Inventory item not found")
    return item


def _recalculate(item: InventoryItem) -> None:
    """Keep planner metrics deterministic and explainable.

    Availability is stock coverage against the planner's required/minimum quantity.
    Reliability is life achievement against expected life using observed average life.
    Criticality here is planning criticality (stock + life risk), not an FMEA severity score.
    """
    if (item.minimum_quantity or 0) > 0:
        item.availability_pct = round(min(100.0, (item.quantity / item.minimum_quantity) * 100.0), 1)
    else:
        item.availability_pct = None

    if (item.expected_life_hours or 0) > 0 and item.observed_avg_life_hours is not None:
        item.reliability_pct = round(min(100.0, (item.observed_avg_life_hours / item.expected_life_hours) * 100.0), 1)
    else:
        item.reliability_pct = None

    availability = item.availability_pct
    reliability = item.reliability_pct
    if availability is None and reliability is None:
        item.criticality = "UNASSESSED"
        return

    if (item.minimum_quantity or 0) > 0 and item.quantity == 0:
        item.criticality = "CRITICAL"
    elif (availability is not None and availability < 50) or (reliability is not None and reliability < 60):
        item.criticality = "CRITICAL"
    elif (availability is not None and availability < 75) or (reliability is not None and reliability < 75):
        item.criticality = "HIGH"
    elif (availability is not None and availability < 100) or (reliability is not None and reliability < 90):
        item.criticality = "MEDIUM"
    else:
        item.criticality = "LOW"


def _transaction_out(tx: InventoryTransaction) -> InventoryTransactionOut:
    return InventoryTransactionOut(
        id=tx.id,
        item_id=tx.item_id,
        item_name=tx.item.name,
        quantity_before=tx.quantity_before,
        quantity_change=tx.quantity_change,
        quantity_after=tx.quantity_after,
        operator=tx.operator,
        reason=tx.reason,
        transaction_type=tx.transaction_type,
        created_at=tx.created_at,
    )


@router.get("/", response_model=list[InventoryOut])
def list_inventory(include_archived: bool = False, db: Session = Depends(get_db)):
    query = db.query(InventoryItem)
    if not include_archived:
        query = query.filter(InventoryItem.is_active.is_(True))
    items = query.order_by(InventoryItem.name.asc()).all()
    changed = False
    for item in items:
        before = (item.availability_pct, item.reliability_pct, item.criticality)
        _recalculate(item)
        after = (item.availability_pct, item.reliability_pct, item.criticality)
        changed = changed or before != after
    if changed:
        db.commit()
    return items


@router.get("/transactions", response_model=list[InventoryTransactionOut])
def list_transactions(item_id: int | None = None, limit: int = 200, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    query = db.query(InventoryTransaction).join(InventoryTransaction.item)
    if item_id is not None:
        query = query.filter(InventoryTransaction.item_id == item_id)
    transactions = query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()
    return [_transaction_out(tx) for tx in transactions]


@router.post("/", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db), _: User = Depends(require_operator)):
    data = payload.model_dump()
    data["availability_pct"] = None
    data["reliability_pct"] = None
    data["criticality"] = "UNASSESSED"
    item = InventoryItem(**data)
    _recalculate(item)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An inventory item with this name already exists")
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InventoryOut)
def update_inventory(item_id: int, payload: InventoryUpdate, db: Session = Depends(get_db), _: User = Depends(require_operator)):
    item = _get_item(db, item_id)
    if not item.is_active:
        raise HTTPException(409, "Archived inventory items cannot be edited")
    data = payload.model_dump(exclude_unset=True)
    for protected in ("availability_pct", "reliability_pct", "criticality"):
        data.pop(protected, None)
    for key, value in data.items():
        setattr(item, key, value)
    _recalculate(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An inventory item with this name already exists")
    db.refresh(item)
    return item


@router.post("/{item_id}/quantity", response_model=InventoryOut)
def change_quantity(item_id: int, payload: InventoryQuantityChange, db: Session = Depends(get_db), user: User = Depends(require_operator)):
    item = _get_item(db, item_id)
    if not item.is_active:
        raise HTTPException(409, "Archived inventory items cannot be adjusted")
    if payload.delta == 0:
        raise HTTPException(400, "Quantity change cannot be zero")
    before = item.quantity
    after = before + payload.delta
    if after < 0:
        raise HTTPException(400, "Quantity cannot be negative")

    item.quantity = after
    _recalculate(item)
    db.add(InventoryTransaction(
        item_id=item.id,
        quantity_before=before,
        quantity_change=payload.delta,
        quantity_after=after,
        operator=(payload.operator.strip() or user.username),
        reason=payload.reason.strip(),
        transaction_type="IN" if payload.delta > 0 else "OUT",
    ))
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/set-quantity", response_model=InventoryOut)
def set_quantity(item_id: int, payload: InventorySetQuantity, db: Session = Depends(get_db), user: User = Depends(require_operator)):
    item = _get_item(db, item_id)
    if not item.is_active:
        raise HTTPException(409, "Archived inventory items cannot be adjusted")
    before = item.quantity
    if payload.quantity == before:
        raise HTTPException(400, "New quantity is the same as current quantity")

    delta = payload.quantity - before
    item.quantity = payload.quantity
    _recalculate(item)
    db.add(InventoryTransaction(
        item_id=item.id,
        quantity_before=before,
        quantity_change=delta,
        quantity_after=payload.quantity,
        operator=(payload.operator.strip() or user.username),
        reason=payload.reason.strip(),
        transaction_type="CORRECTION",
    ))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", response_model=InventoryOut)
def archive_inventory(item_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = _get_item(db, item_id)
    if not item.is_active:
        return item
    item.is_active = False
    db.commit()
    db.refresh(item)
    return item
