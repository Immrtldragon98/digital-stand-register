from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import LocationEnum, StatusEnum
from app.models.stand_asset import StandAsset
from app.models.stand_change_event import StandChangeEvent
from app.models.stand_installation import StandInstallation
from app.models.stand_preparation_event import StandPreparationEvent
from app.models.stand_position import Position


PREPARATION_FLOW = [
    StatusEnum.YET_TO_READY,
    StatusEnum.PENDING,
    StatusEnum.GAUGING,
    StatusEnum.HYDROTEST,
    StatusEnum.READY,
]


class OperationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _elapsed_hours(start: datetime, end: datetime) -> float:
        return round(max(0.0, (end - start).total_seconds() / 3600.0), 2)

    def _get_stand_locked(self, code: str) -> StandAsset:
        stand = self.db.query(StandAsset).filter(StandAsset.code == code).with_for_update().first()
        if not stand:
            raise HTTPException(status_code=404, detail=f"Stand {code} not found.")
        return stand

    def _get_position_locked(self, position_id: int) -> Position:
        position = self.db.query(Position).filter(Position.id == position_id).with_for_update().first()
        if not position:
            raise HTTPException(status_code=404, detail="Position not found.")
        return position

    def _commit_or_conflict(self, detail: str):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail=detail) from exc

    def install_stand(self, stand_code: str, position_id: int, user_id: int | None, operator_name: str | None = None):
        stand = self._get_stand_locked(stand_code)
        self._get_position_locked(position_id)
        if stand.current_status != StatusEnum.READY:
            raise HTTPException(status_code=400, detail="Stand must be READY before installation.")
        if stand.current_position_id is not None or stand.current_location == LocationEnum.WRM_LINE:
            raise HTTPException(status_code=409, detail="Stand is already assigned to a running position.")
        occupied = self.db.query(StandInstallation).filter(
            StandInstallation.position_id == position_id,
            StandInstallation.removed_at.is_(None),
        ).first()
        if occupied:
            raise HTTPException(status_code=409, detail="Position already has an installed stand.")
        now = datetime.utcnow()
        stand.current_location = LocationEnum.WRM_LINE
        stand.current_status = StatusEnum.INSTALLED
        stand.current_position_id = position_id
        self.db.add(StandInstallation(stand_id=stand.id, position_id=position_id, installed_at=now, installed_by=operator_name))
        self.db.add(ActivityLog(user_id=user_id, action="INSTALL_STAND", timestamp=now, details=f"Stand {stand.code} installed at Position ID {position_id} by {operator_name or 'not recorded'}."))
        self._commit_or_conflict("Stand or position was changed by another user. Refresh and try again.")
        return {"status": "success", "message": f"Stand {stand.code} successfully installed."}

    def remove_stand(self, stand_code: str, user_id: int | None, operator_name: str | None = None, reason: str | None = None):
        stand = self._get_stand_locked(stand_code)
        if stand.current_location != LocationEnum.WRM_LINE or stand.current_status != StatusEnum.INSTALLED:
            raise HTTPException(status_code=400, detail="Stand must be installed before removal.")
        active = self.db.query(StandInstallation).filter(
            StandInstallation.stand_id == stand.id,
            StandInstallation.removed_at.is_(None),
        ).with_for_update().first()
        if not active:
            raise HTTPException(status_code=409, detail="Active installation record is missing.")
        now = datetime.utcnow()
        hours = self._elapsed_hours(active.installed_at, now)
        active.removed_at = now
        active.removed_by = operator_name
        active.removal_reason = reason
        active.campaign_hours = hours
        stand.lifetime_hours = round((stand.lifetime_hours or 0.0) + hours, 2)
        stand.current_location = LocationEnum.WIP
        stand.current_status = StatusEnum.PENDING
        stand.current_position_id = None
        self.db.add(ActivityLog(user_id=user_id, action="REMOVE_STAND", timestamp=now, details=f"Stand {stand.code} removed to PENDING. Reason: {reason or 'not recorded'}. Operator: {operator_name or 'not recorded'}."))
        self._commit_or_conflict("Stand removal conflicted with another update.")
        return {"status": "success", "message": f"Stand {stand.code} removed and marked PENDING.", "campaign_hours": hours, "lifetime_hours": stand.lifetime_hours}

    def change_stand(self, payload, user_id: int | None):
        if payload.removed_stand_code == payload.installed_stand_code:
            raise HTTPException(status_code=400, detail="Removed and replacement stand cannot be the same asset.")
        self._get_position_locked(payload.position_id)
        removed = self._get_stand_locked(payload.removed_stand_code)
        installed = self._get_stand_locked(payload.installed_stand_code)
        if removed.current_position_id != payload.position_id or removed.current_status != StatusEnum.INSTALLED:
            raise HTTPException(status_code=400, detail="Removed stand is not installed at the selected position.")
        if installed.current_status != StatusEnum.READY:
            raise HTTPException(status_code=400, detail="Replacement stand must be READY.")
        if installed.current_position_id is not None or installed.current_location == LocationEnum.WRM_LINE:
            raise HTTPException(status_code=409, detail="Replacement stand is already running in another position.")
        active = self.db.query(StandInstallation).filter(
            StandInstallation.stand_id == removed.id,
            StandInstallation.position_id == payload.position_id,
            StandInstallation.removed_at.is_(None),
        ).with_for_update().first()
        if not active:
            raise HTTPException(status_code=409, detail="Active installation record not found.")

        now = datetime.utcnow()
        change_time = payload.changed_at or now
        if change_time.tzinfo is not None:
            change_time = change_time.astimezone().replace(tzinfo=None)
        if change_time > now + timedelta(minutes=5):
            raise HTTPException(status_code=400, detail="Stand change time cannot be in the future.")
        if change_time < active.installed_at:
            raise HTTPException(status_code=400, detail="Stand change time cannot be before the current stand was installed.")

        hours = self._elapsed_hours(active.installed_at, change_time)
        active.removed_at = change_time
        active.removed_by = payload.changed_by
        active.removal_reason = payload.reason
        active.campaign_hours = hours
        removed.lifetime_hours = round((removed.lifetime_hours or 0.0) + hours, 2)
        removed.current_location = LocationEnum.WIP
        removed.current_status = StatusEnum.PENDING
        removed.current_position_id = None
        removed.leakage = payload.leakage
        removed.vibration = payload.vibration
        removed.condition_notes = payload.removed_condition or payload.notes

        installed.current_location = LocationEnum.WRM_LINE
        installed.current_status = StatusEnum.INSTALLED
        installed.current_position_id = payload.position_id
        self.db.add(StandInstallation(stand_id=installed.id, position_id=payload.position_id, installed_at=change_time, installed_by=payload.changed_by))
        self.db.add(StandChangeEvent(position_id=payload.position_id, removed_stand_id=removed.id, installed_stand_id=installed.id, changed_at=change_time, changed_by=payload.changed_by, reason=payload.reason, notes=payload.notes, removed_condition=payload.removed_condition))
        self.db.add(ActivityLog(user_id=user_id, action="CHANGE_STAND", timestamp=change_time, details=f"Position {payload.position_id}: {removed.code} -> {installed.code}. Reason: {payload.reason}. Operator: {payload.changed_by}."))
        self._commit_or_conflict("Another user changed this stand or position.")
        return {"status": "success", "removed_stand": removed.code, "installed_stand": installed.code, "changed_at": change_time, "removed_campaign_hours": hours, "removed_lifetime_hours": removed.lifetime_hours, "removed_new_status": StatusEnum.PENDING, "installed_new_status": StatusEnum.INSTALLED}

    def update_preparation_status(self, stand_code: str, status: StatusEnum, user_id: int | None, updated_by: str, remarks: str | None = None):
        stand = self._get_stand_locked(stand_code)
        if status not in PREPARATION_FLOW:
            raise HTTPException(status_code=400, detail="Invalid preparation status.")
        if stand.current_status == StatusEnum.INSTALLED or stand.current_position_id is not None:
            raise HTTPException(status_code=400, detail="Running stand cannot be moved through preparation workflow.")

        current = stand.current_status
        if current == StatusEnum.INP:
            current = StatusEnum.PENDING
            stand.current_status = StatusEnum.PENDING
        if current not in PREPARATION_FLOW:
            raise HTTPException(status_code=400, detail="Stand is not in the preparation workflow.")

        current_index = PREPARATION_FLOW.index(current)
        target_index = PREPARATION_FLOW.index(status)
        is_next_step = target_index == current_index + 1
        is_rework_reset = status == StatusEnum.PENDING and current != StatusEnum.YET_TO_READY
        if not (is_next_step or is_rework_reset):
            expected = PREPARATION_FLOW[current_index + 1].value if current_index < len(PREPARATION_FLOW) - 1 else "PENDING (for rework)"
            raise HTTPException(status_code=400, detail=f"Next allowed status: {expected}.")

        operator = updated_by.strip()
        if not operator:
            raise HTTPException(status_code=400, detail="Name is required.")
        now = datetime.utcnow()
        stand.current_status = status
        stand.current_location = LocationEnum.READY_AREA if status == StatusEnum.READY else LocationEnum.WIP
        self.db.add(StandPreparationEvent(stand_id=stand.id, from_status=current, to_status=status, updated_by=operator, remarks=(remarks or "").strip() or None, changed_at=now))
        if status in {StatusEnum.GAUGING, StatusEnum.HYDROTEST, StatusEnum.READY}:
            self.db.add(ActivityLog(user_id=user_id, action=f"{status.value}_COMPLETE", timestamp=now, details=f"Stand {stand.code}: {status.value} completed by {operator}. Remarks: {(remarks or 'not recorded').strip() or 'not recorded'}."))
        self._commit_or_conflict("Stand status was changed by another user.")
        return {"status": "success", "stand_code": stand.code, "old_status": current, "new_status": status, "updated_by": operator, "remarks": (remarks or "").strip() or None, "changed_at": now}

    def mark_stand_ready(self, stand_code: str, user_id: int | None, updated_by: str = "System"):
        return self.update_preparation_status(stand_code, StatusEnum.READY, user_id, updated_by)
