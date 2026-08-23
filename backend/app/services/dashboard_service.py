from datetime import datetime
from sqlalchemy.orm import Session
from app.models.line import Line
from app.models.stand_installation import StandInstallation
from app.models.entry_guide_installation import EntryGuideInstallation


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _hours(start: datetime) -> float:
        return round(max(0.0, (datetime.utcnow() - start).total_seconds() / 3600.0), 2)

    def get_plant_dashboard(self):
        lines = self.db.query(Line).order_by(Line.id).all()
        dashboard_data = []

        for line in lines:
            line_positions = []
            for pos in sorted(line.positions, key=lambda p: p.position_number):
                active_stand = self.db.query(StandInstallation).filter(
                    StandInstallation.position_id == pos.id,
                    StandInstallation.removed_at.is_(None),
                ).first()

                active_guide = None
                if pos.position_number in {2, 4, 6, 8, 10}:
                    active_guide = self.db.query(EntryGuideInstallation).filter(
                        EntryGuideInstallation.position_id == pos.id,
                        EntryGuideInstallation.removed_at.is_(None),
                    ).first()

                line_positions.append({
                    "id": pos.id,
                    "position_number": pos.position_number,
                    "entry_guide_applicable": pos.position_number in {2, 4, 6, 8, 10},
                    "current_stand": {
                        "id": active_stand.stand.id,
                        "code": active_stand.stand.code,
                        "installed_at": active_stand.installed_at,
                        "campaign_hours": self._hours(active_stand.installed_at),
                        "lifetime_hours": round((active_stand.stand.lifetime_hours or 0.0) + self._hours(active_stand.installed_at), 2),
                        "leakage": active_stand.stand.leakage,
                        "vibration": active_stand.stand.vibration,
                    } if active_stand else None,
                    "current_guide": {
                        "id": active_guide.guide.id,
                        "code": active_guide.guide.code,
                        "condition": active_guide.guide.condition,
                        "installed_at": active_guide.installed_at,
                        "campaign_hours": self._hours(active_guide.installed_at),
                        "lifetime_hours": round((active_guide.guide.lifetime_hours or 0.0) + self._hours(active_guide.installed_at), 2),
                    } if active_guide else None,
                })

            dashboard_data.append({"id": line.id, "name": line.name, "positions": line_positions})

        return dashboard_data
