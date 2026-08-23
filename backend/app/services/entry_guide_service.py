from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.entry_guide_repository import EntryGuideRepository
from app.models.enums import LocationEnum, StatusEnum
from app.models.entry_guide_installation import EntryGuideInstallation
from app.models.stand_position import Position
from app.models.activity_log import ActivityLog


GUIDE_POSITIONS = {2, 4, 6, 8, 10}


class EntryGuideService:
    def __init__(self, db: Session):
        self.db = db
        self.guide_repo = EntryGuideRepository(db)

    @staticmethod
    def _elapsed_hours(start: datetime, end: datetime) -> float:
        return round(max(0.0, (end - start).total_seconds() / 3600.0), 2)

    def _validate_position(self, position_id: int):
        position = self.db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        if position.position_number not in GUIDE_POSITIONS:
            raise HTTPException(status_code=400, detail="Entry guides are only used at positions 2, 4, 6, 8 and 10.")
        return position

    def install_guide(self, guide_code: str, position_id: int, user_id: int, operator_name: str | None = None):
        self._validate_position(position_id)
        guide = self.guide_repo.get_by_code(guide_code)
        if not guide:
            raise HTTPException(status_code=404, detail="Entry guide asset not found")
        if guide.current_status != StatusEnum.READY:
            raise HTTPException(status_code=400, detail="Entry guide must be READY before installation.")

        occupied = self.db.query(EntryGuideInstallation).filter(
            EntryGuideInstallation.position_id == position_id,
            EntryGuideInstallation.removed_at.is_(None),
        ).first()
        if occupied:
            raise HTTPException(status_code=400, detail="Position already has an installed entry guide.")

        now = datetime.utcnow()
        guide.current_location = LocationEnum.WRM_LINE
        guide.current_status = StatusEnum.INSTALLED
        guide.current_position_id = position_id
        self.db.add(EntryGuideInstallation(
            guide_id=guide.id,
            position_id=position_id,
            installed_at=now,
            installed_by=operator_name,
        ))
        self.db.add(ActivityLog(
            user_id=user_id,
            action="INSTALL_ENTRY_GUIDE",
            timestamp=now,
            details=f"Entry guide {guide.code} installed at Position ID {position_id} by {operator_name or 'system user'}.",
        ))
        self.db.commit()
        return {"status": "success", "message": f"Entry guide {guide.code} successfully installed."}

    def remove_guide(self, guide_code: str, removed_by: str, removal_reason: str, user_id: int):
        guide = self.guide_repo.get_by_code(guide_code)
        if not guide:
            raise HTTPException(status_code=404, detail="Entry guide asset not found")
        active = self.db.query(EntryGuideInstallation).filter(
            EntryGuideInstallation.guide_id == guide.id,
            EntryGuideInstallation.removed_at.is_(None),
        ).first()
        if not active:
            raise HTTPException(status_code=400, detail="Entry guide is not currently installed.")

        now = datetime.utcnow()
        hours = self._elapsed_hours(active.installed_at, now)
        active.removed_at = now
        active.removed_by = removed_by
        active.removal_reason = removal_reason
        active.campaign_hours = hours
        guide.lifetime_hours = round((guide.lifetime_hours or 0.0) + hours, 2)
        guide.current_location = LocationEnum.WIP
        guide.current_status = StatusEnum.PENDING
        guide.current_position_id = None

        self.db.add(ActivityLog(
            user_id=user_id,
            action="REMOVE_ENTRY_GUIDE",
            timestamp=now,
            details=f"Entry guide {guide.code} removed by {removed_by}. Reason: {removal_reason}.",
        ))
        self.db.commit()
        return {"status": "success", "campaign_hours": hours, "new_status": StatusEnum.PENDING}

    def update_condition(self, guide_code: str, condition, notes: str | None, user_id: int):
        guide = self.guide_repo.get_by_code(guide_code)
        if not guide:
            raise HTTPException(status_code=404, detail="Entry guide asset not found")
        guide.condition = condition
        guide.condition_notes = notes
        self.db.add(ActivityLog(
            user_id=user_id,
            action="UPDATE_ENTRY_GUIDE_CONDITION",
            timestamp=datetime.utcnow(),
            details=f"Entry guide {guide.code} condition set to {condition.value}. Notes: {notes or '-'}",
        ))
        self.db.commit()
        return {"status": "success", "guide_code": guide.code, "condition": condition}
