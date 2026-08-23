from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.stand_repository import StandRepository
from app.models.stand_installation import StandInstallation
from app.models.entry_guide_installation import EntryGuideInstallation
from app.models.stand_position import Position
from app.models.stand_preparation_event import StandPreparationEvent


class StandService:
    def __init__(self, db: Session):
        self.db = db
        self.stand_repo = StandRepository(db)

    @staticmethod
    def _hours(start: datetime, end: datetime) -> float:
        return round(max(0.0, (end - start).total_seconds() / 3600.0), 2)

    def get_all_stands(self):
        return [
            {
                "id": stand.id,
                "code": stand.code,
                "current_location": stand.current_location,
                "current_status": stand.current_status,
                "current_position_id": stand.current_position_id,
                "lifetime_hours": stand.lifetime_hours,
                "leakage": stand.leakage,
                "vibration": stand.vibration,
            }
            for stand in self.stand_repo.get_all()
        ]

    def get_stand_details(self, stand_id: int):
        stand = self.stand_repo.get_by_id(stand_id)
        if not stand:
            raise HTTPException(status_code=404, detail="Stand not found")

        installations = self.db.query(StandInstallation).filter(
            StandInstallation.stand_id == stand_id
        ).order_by(StandInstallation.installed_at.desc()).all()

        active = next((x for x in installations if x.removed_at is None), None)
        current_campaign_hours = self._hours(active.installed_at, datetime.utcnow()) if active else 0.0
        total_hours = round((stand.lifetime_hours or 0.0) + current_campaign_hours, 2)

        current_position = None
        current_guide = None
        if stand.current_position_id:
            current_position = self.db.query(Position).filter(Position.id == stand.current_position_id).first()
            if current_position and current_position.position_number in {2, 4, 6, 8, 10}:
                guide_inst = self.db.query(EntryGuideInstallation).filter(
                    EntryGuideInstallation.position_id == current_position.id,
                    EntryGuideInstallation.removed_at.is_(None),
                ).first()
                if guide_inst:
                    guide_campaign = self._hours(guide_inst.installed_at, datetime.utcnow())
                    guide_history = self.db.query(EntryGuideInstallation).filter(
                        EntryGuideInstallation.guide_id == guide_inst.guide.id
                    ).order_by(EntryGuideInstallation.installed_at.desc()).all()
                    current_guide = {
                        "id": guide_inst.guide.id,
                        "code": guide_inst.guide.code,
                        "condition": guide_inst.guide.condition,
                        "condition_notes": guide_inst.guide.condition_notes,
                        "lifetime_hours": round((guide_inst.guide.lifetime_hours or 0.0) + guide_campaign, 2),
                        "current_campaign_hours": guide_campaign,
                        "installed_at": guide_inst.installed_at,
                        "history": [
                            {
                                "position_id": item.position_id,
                                "installed_at": item.installed_at,
                                "removed_at": item.removed_at,
                                "campaign_hours": item.campaign_hours,
                                "installed_by": item.installed_by,
                                "removed_by": item.removed_by,
                                "removal_reason": item.removal_reason,
                            }
                            for item in guide_history
                        ],
                    }

        history = [{
            "position_id": inst.position_id,
            "installed_at": inst.installed_at,
            "removed_at": inst.removed_at,
            "campaign_hours": inst.campaign_hours,
            "installed_by": inst.installed_by,
            "removed_by": inst.removed_by,
            "removal_reason": inst.removal_reason,
        } for inst in installations]

        preparation_events = self.db.query(StandPreparationEvent).filter(
            StandPreparationEvent.stand_id == stand_id
        ).order_by(StandPreparationEvent.changed_at.desc()).all()
        preparation_history = [{
            "from_status": event.from_status,
            "to_status": event.to_status,
            "updated_by": event.updated_by,
            "remarks": event.remarks,
            "changed_at": event.changed_at,
        } for event in preparation_events]

        return {
            "id": stand.id,
            "code": stand.code,
            "current_location": stand.current_location,
            "current_status": stand.current_status,
            "current_position_id": stand.current_position_id,
            "lifetime_hours": total_hours,
            "current_campaign_hours": current_campaign_hours,
            "leakage": stand.leakage,
            "vibration": stand.vibration,
            "condition_notes": stand.condition_notes,
            "entry_guide": current_guide,
            "history": history,
            "preparation_history": preparation_history,
        }
