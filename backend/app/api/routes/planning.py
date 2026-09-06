import re
from datetime import datetime, timezone
from statistics import mean

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_operator
from app.database.session import get_db
from app.models.enums import StatusEnum
from app.models.line import Line
from app.models.reliability_history import HistoricalCampaign
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.stand_position import Position
from app.models.user import User

router = APIRouter()


class TargetLifeUpdate(BaseModel):
    target_life_hours: float | None = Field(default=None, gt=0)


def _position_from_code(code: str):
    match = re.match(r"^0*(10|[1-9])", (code or "").strip())
    return int(match.group(1)) if match else None


@router.get("/summary")
def planning_summary(db: Session = Depends(get_db)):
    positions = db.query(Position, Line).join(Line, Position.line_id == Line.id).order_by(Line.name, Position.position_number).all()
    active = {
        row.position_id: row
        for row in db.query(StandInstallation).filter(StandInstallation.removed_at.is_(None)).all()
    }
    stands = {s.id: s for s in db.query(StandAsset).all()}
    ready_counts = {i: 0 for i in range(1, 11)}
    for stand in stands.values():
        if stand.current_status == StatusEnum.READY:
            p = _position_from_code(stand.code)
            if p:
                ready_counts[p] += 1

    history = db.query(HistoricalCampaign).filter(HistoricalCampaign.life_days.isnot(None)).all()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = []
    for position, line in positions:
        inst = active.get(position.id)
        stand = stands.get(inst.stand_id) if inst else None
        current_hours = None
        if inst:
            current_hours = max(0.0, (now - inst.installed_at).total_seconds() / 3600.0)
        hist = [h.life_days for h in history if h.line_name == line.name and h.position_number == position.position_number and h.life_days is not None and h.life_days >= 0]
        hist_avg_days = round(mean(hist), 2) if hist else None
        target = position.target_life_hours
        life_pct = round((current_hours / target) * 100, 1) if current_hours is not None and target else None
        if life_pct is None:
            risk = "NO_TARGET"
        elif life_pct >= 95 and ready_counts[position.position_number] == 0:
            risk = "CRITICAL"
        elif life_pct >= 90:
            risk = "HIGH"
        elif life_pct >= 75:
            risk = "WATCH"
        else:
            risk = "LOW"
        result.append({
            "line": line.name,
            "position_id": position.id,
            "position": position.position_number,
            "stand": stand.code if stand else None,
            "installed_at": inst.installed_at.isoformat() if inst else None,
            "running_hours": round(current_hours, 1) if current_hours is not None else None,
            "target_life_hours": target,
            "life_percent": life_pct,
            "historical_avg_days": hist_avg_days,
            "historical_campaigns": len(hist),
            "ready_count": ready_counts[position.position_number],
            "risk": risk,
        })
    return result


@router.patch("/positions/{position_id}/target")
def update_target(position_id: int, payload: TargetLifeUpdate, db: Session = Depends(get_db), _: User = Depends(require_operator)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(404, "Position not found")
    position.target_life_hours = payload.target_life_hours
    db.commit()
    db.refresh(position)
    return {"position_id": position.id, "target_life_hours": position.target_life_hours}
