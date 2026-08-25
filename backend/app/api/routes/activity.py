from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, aliased

from app.database.session import get_db
from app.models.enums import StatusEnum
from app.models.stand_asset import StandAsset
from app.models.stand_change_event import StandChangeEvent
from app.models.stand_preparation_event import StandPreparationEvent

router = APIRouter()


@router.get("/")
def get_activity_logs(db: Session = Depends(get_db)):
    removed = aliased(StandAsset)
    installed = aliased(StandAsset)

    changes = (
        db.query(StandChangeEvent, removed.code, installed.code)
        .join(removed, StandChangeEvent.removed_stand_id == removed.id)
        .join(installed, StandChangeEvent.installed_stand_id == installed.id)
        .order_by(StandChangeEvent.changed_at.desc())
        .limit(100)
        .all()
    )

    prep = (
        db.query(StandPreparationEvent, StandAsset.code)
        .join(StandAsset, StandPreparationEvent.stand_id == StandAsset.id)
        .filter(StandPreparationEvent.to_status.in_([
            StatusEnum.GAUGING,
            StatusEnum.HYDROTEST,
            StatusEnum.READY,
        ]))
        .order_by(StandPreparationEvent.changed_at.desc())
        .limit(100)
        .all()
    )

    rows = []
    for event, old_code, new_code in changes:
        rows.append({
            "date": event.changed_at,
            "activity": "Stand Change",
            "stand": f"{old_code} → {new_code}",
            "done_by": event.changed_by,
            "details": event.reason,
        })

    labels = {
        StatusEnum.GAUGING: "Gauging",
        StatusEnum.HYDROTEST: "Hydrotest",
        StatusEnum.READY: "Ready",
    }
    for event, code in prep:
        rows.append({
            "date": event.changed_at,
            "activity": labels.get(event.to_status, event.to_status.value),
            "stand": code,
            "done_by": event.updated_by,
            "details": event.remarks or "",
        })

    rows.sort(key=lambda row: row["date"], reverse=True)
    return rows[:200]
