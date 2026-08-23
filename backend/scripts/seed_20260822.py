"""Idempotent one-time seed for the 22/08/2026 stand-area snapshot.

Run after migrations:
    cd backend
    python scripts/seed_20260822.py

The seed never invents the four stand codes absent from the shift report. Those
assets can be added later through the normal stand master workflow once codes are
confirmed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.session import SessionLocal
from app.models.enums import LocationEnum, StatusEnum
from app.models.line import Line
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.stand_position import Position
from app.seed.snapshot_20260822 import RUNNING_LINES, SNAPSHOT_AT, all_known_codes, normalized_spares, validate_snapshot


def get_or_create_line(db, name: str) -> Line:
    line = db.query(Line).filter(Line.name == name).first()
    if not line:
        line = Line(name=name)
        db.add(line)
        db.flush()
    return line


def ensure_positions(db, line: Line) -> dict[int, Position]:
    positions = {p.position_number: p for p in line.positions}
    for number in range(1, 11):
        if number not in positions:
            p = Position(line_id=line.id, position_number=number)
            db.add(p)
            db.flush()
            positions[number] = p
    return positions


def get_or_create_stand(db, code: str) -> StandAsset:
    stand = db.query(StandAsset).filter(StandAsset.code == code).first()
    if not stand:
        stand = StandAsset(
            code=code,
            current_location=LocationEnum.WIP,
            current_status=StatusEnum.YET_TO_READY,
            lifetime_hours=0.0,
        )
        db.add(stand)
        db.flush()
    return stand


def seed() -> None:
    validation = validate_snapshot()
    if validation.duplicate_running_codes:
        raise RuntimeError(f"Duplicate running stand codes: {validation.duplicate_running_codes}")
    if validation.running_spare_overlap:
        raise RuntimeError(f"Running/spare overlap after normalization: {validation.running_spare_overlap}")

    db = SessionLocal()
    try:
        # Ensure all known physical assets exist first.
        for code in sorted(all_known_codes()):
            get_or_create_stand(db, code)

        line_positions: dict[str, dict[int, Position]] = {}
        for line_name in ("W1", "W2", "W3"):
            line = get_or_create_line(db, line_name)
            line_positions[line_name] = ensure_positions(db, line)

        # Clear only active assignments for stands/positions represented by this baseline.
        # Historical rows are left untouched; this makes rerunning the seed safe after a
        # partially completed commissioning attempt.
        known_ids = [s.id for s in db.query(StandAsset).filter(StandAsset.code.in_(all_known_codes())).all()]
        db.query(StandInstallation).filter(
            StandInstallation.stand_id.in_(known_ids),
            StandInstallation.removed_at.is_(None),
        ).delete(synchronize_session=False)

        # Reset known stands before applying the normalized snapshot.
        for stand in db.query(StandAsset).filter(StandAsset.id.in_(known_ids)).all():
            stand.current_position_id = None
            stand.current_location = LocationEnum.WIP
            stand.current_status = StatusEnum.YET_TO_READY

        # Running arrangements from the report.
        for line_name, stand_codes in RUNNING_LINES.items():
            for position_number, code in enumerate(stand_codes, start=1):
                stand = get_or_create_stand(db, code)
                position = line_positions[line_name][position_number]
                stand.current_position_id = position.id
                stand.current_location = LocationEnum.WRM_LINE
                stand.current_status = StatusEnum.INSTALLED
                db.add(StandInstallation(
                    stand_id=stand.id,
                    position_id=position.id,
                    installed_at=SNAPSHOT_AT,
                    installed_by="22/08/2026 baseline import",
                ))

        # Preparation-area states after applying Running > Ready > INP > Pending.
        for code, state in normalized_spares().items():
            stand = get_or_create_stand(db, code)
            if state == "READY":
                stand.current_status = StatusEnum.READY
                stand.current_location = LocationEnum.READY_AREA
            elif state == "INP":
                stand.current_status = StatusEnum.INP
                stand.current_location = LocationEnum.WIP
            else:
                stand.current_status = StatusEnum.PENDING
                stand.current_location = LocationEnum.WIP

        db.commit()

        print("22/08/2026 snapshot imported successfully")
        print(f"Running: {validation.running_count}")
        print(f"Spare/preparation: {validation.spare_count}")
        print(f"Known assets in report: {validation.known_total}/{validation.expected_total}")
        if validation.unidentified_count:
            print(
                f"WARNING: {validation.unidentified_count} stand asset codes are not present in the supplied report. "
                "They were not invented or seeded."
            )
        print("Life baseline for initially-running stands begins at 22/08/2026 00:00 because earlier installation times were not supplied.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
