from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_operator
from app.database.session import get_db
from app.models.stand_asset import StandAsset
from app.models.stand_event import StandCampaignEvent
from app.models.stand_installation import StandInstallation
from app.models.user import User

router = APIRouter()

CATEGORIES = {"BREAKDOWN", "OBSERVATION", "QUALITY", "COMPONENT", "MAINTENANCE"}
SEVERITIES = {"LOW", "MEDIUM", "HIGH", "STOPPAGE"}


class EventInput(BaseModel):
    category: str = Field(default="OBSERVATION", max_length=24)
    event_type: str = Field(min_length=1, max_length=100)
    severity: str = Field(default="LOW", max_length=16)
    component_name: str | None = Field(default=None, max_length=100)
    duration_minutes: float | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)
    action_taken: str | None = Field(default=None, max_length=2000)
    event_at: datetime | None = None


def _payload(row: StandCampaignEvent):
    return {
        "id": row.id,
        "stand_id": row.stand_id,
        "installation_id": row.installation_id,
        "category": row.category,
        "event_type": row.event_type,
        "severity": row.severity,
        "component_name": row.component_name,
        "duration_minutes": row.duration_minutes,
        "description": row.description,
        "action_taken": row.action_taken,
        "event_at": row.event_at,
        "recorded_by": row.recorded_by,
    }


@router.get("/stand/{stand_id}")
def list_stand_events(stand_id: int, db: Session = Depends(get_db)):
    if not db.get(StandAsset, stand_id):
        raise HTTPException(404, "Stand not found")
    rows = db.query(StandCampaignEvent).filter(
        StandCampaignEvent.stand_id == stand_id
    ).order_by(StandCampaignEvent.event_at.desc()).all()
    return [_payload(row) for row in rows]


@router.post("/stand/{stand_id}")
def create_stand_event(
    stand_id: int,
    payload: EventInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    stand = db.get(StandAsset, stand_id)
    if not stand:
        raise HTTPException(404, "Stand not found")

    active = db.query(StandInstallation).filter(
        StandInstallation.stand_id == stand_id,
        StandInstallation.removed_at.is_(None),
    ).first()
    if not active:
        raise HTTPException(400, "Events can be logged only while the stand is installed and running.")

    category = payload.category.strip().upper()
    severity = payload.severity.strip().upper()
    if category not in CATEGORIES:
        raise HTTPException(400, f"Category must be one of: {', '.join(sorted(CATEGORIES))}")
    if severity not in SEVERITIES:
        raise HTTPException(400, f"Severity must be one of: {', '.join(sorted(SEVERITIES))}")

    row = StandCampaignEvent(
        stand_id=stand_id,
        installation_id=active.id,
        category=category,
        event_type=payload.event_type.strip(),
        severity=severity,
        component_name=(payload.component_name or "").strip() or None,
        duration_minutes=payload.duration_minutes,
        description=(payload.description or "").strip() or None,
        action_taken=(payload.action_taken or "").strip() or None,
        event_at=payload.event_at or datetime.utcnow(),
        recorded_by=user.username,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _payload(row)
