from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session, joinedload
from app.models.line import Line
from app.models.stand_installation import StandInstallation
from app.models.entry_guide_installation import EntryGuideInstallation
from app.services.runtime_service import RuntimeService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _hours(start: datetime) -> float:
        return round(max(0.0, (datetime.utcnow() - start).total_seconds() / 3600.0), 2)

    def get_plant_dashboard(self):
        lines = (
            self.db.query(Line)
            .options(joinedload(Line.positions))
            .order_by(Line.id)
            .all()
        )

        stand_installations = (
            self.db.query(StandInstallation)
            .options(joinedload(StandInstallation.stand))
            .filter(StandInstallation.removed_at.is_(None))
            .all()
        )
        stands_by_position = {item.position_id: item for item in stand_installations}

        guide_installations = (
            self.db.query(EntryGuideInstallation)
            .options(joinedload(EntryGuideInstallation.guide))
            .filter(EntryGuideInstallation.removed_at.is_(None))
            .all()
        )
        guides_by_position = {item.position_id: item for item in guide_installations}

        runtime = RuntimeService(self.db)
        as_of = datetime.utcnow()
        histories = defaultdict(list)
        for item in self.db.query(StandInstallation).filter(StandInstallation.stand_id.in_([x.stand_id for x in stand_installations])).all():
            histories[item.stand_id].append(item)
        guide_histories = defaultdict(list)
        for item in self.db.query(EntryGuideInstallation).filter(EntryGuideInstallation.guide_id.in_([x.guide_id for x in guide_installations])).all():
            guide_histories[item.guide_id].append(item)
        dashboard_data = []
        for line in lines:
            line_positions = []
            for pos in sorted(line.positions, key=lambda p: p.position_number):
                active_stand = stands_by_position.get(pos.id)
                active_guide = guides_by_position.get(pos.id) if pos.position_number in {2, 4, 6, 8, 10} else None

                stand_payload = None
                if active_stand:
                    reading = runtime.installation(active_stand, as_of)
                    campaign_hours = reading["hours"]
                    target = pos.target_life_hours
                    life_percent = round((campaign_hours / target) * 100, 1) if target and campaign_hours is not None else None
                    remaining_hours = round(max(0.0, target - campaign_hours), 1) if target and campaign_hours is not None else None
                    stand_payload = {
                        "id": active_stand.stand.id,
                        "code": active_stand.stand.code,
                        "installed_at": active_stand.installed_at,
                        "campaign_hours": campaign_hours,
                        "target_life_hours": target,
                        "life_percent": life_percent,
                        "remaining_hours": remaining_hours,
                        **runtime.stand_runtime(active_stand.stand, histories[active_stand.stand_id], as_of),
                        "known_runtime_hours": reading["known_hours"] if reading['has_coverage'] else None,
                        "runtime_complete": reading["complete"], "elapsed_hours": reading["elapsed_hours"],
                        "coverage_status": reading['coverage_status'], "observed_from": reading['observed_from'],
                        "ongoing": True, "duration_basis": "ACTUAL_MILL_RUNTIME" if reading['complete'] else "RUNTIME_INCOMPLETE",
                        "leakage": active_stand.stand.leakage,
                        "vibration": active_stand.stand.vibration,
                        "abnormal_sound": active_stand.stand.abnormal_sound,
                        "condition_notes": active_stand.stand.condition_notes,
                        "health": "ATTENTION" if (active_stand.stand.leakage or active_stand.stand.vibration or active_stand.stand.abnormal_sound) else "NORMAL",
                    }

                guide_reading = runtime.installation(active_guide, as_of) if active_guide else None
                line_positions.append({
                    "id": pos.id,
                    "position_number": pos.position_number,
                    "entry_guide_applicable": pos.position_number in {2, 4, 6, 8, 10},
                    "current_stand": stand_payload,
                    "current_guide": {
                        "id": active_guide.guide.id,
                        "code": active_guide.guide.code,
                        "condition": active_guide.guide.condition,
                        "installed_at": active_guide.installed_at,
                        "campaign_hours": guide_reading["hours"],
                        "known_runtime_hours": guide_reading["known_hours"] if guide_reading["has_coverage"] else None,
                        "runtime_complete": guide_reading["complete"],
                        "elapsed_hours": guide_reading['elapsed_hours'], "coverage_status": guide_reading['coverage_status'],
                        **runtime.stand_runtime(active_guide.guide, guide_histories[active_guide.guide_id], as_of),
                    } if active_guide else None,
                })

            dashboard_data.append({"id": line.id, "name": line.name, "positions": line_positions})

        return dashboard_data
