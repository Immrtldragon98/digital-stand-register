from collections import Counter, defaultdict
from datetime import timedelta
from statistics import mean, median

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.line import Line
from app.models.reliability_history import HistoricalCampaign, HistoricalSpareUsage, ProcessObservation
from app.models.stand_event import StandCampaignEvent
from app.models.stand_installation import StandInstallation
from app.models.stand_position import Position

router = APIRouter()

CAUSE_RULES = [
    ("ROUTINE_CHANGE", ["routine change", "routine"]),
    ("FLATNESS", ["flatness", "flat"]),
    ("INTERNAL_LEAKAGE", ["internal leakage"]),
    ("LEAKAGE", ["leakage", "leak"]),
    ("ENTRY_GUIDE", ["entry guide", "guide jam", "guide"]),
    ("NOZZLE_JAM", ["nozzle jam", "nozzle"]),
    ("COBBLE", ["cobble"]),
    ("ROUGH_SURFACE", ["rough surface", "surface"]),
    ("TRIANGULAR_ROD", ["triangular", "triangle"]),
    ("RIBS", ["ribs", "rib"]),
    ("PLAY", ["play"]),
    ("VIBRATION", ["vibration"]),
    ("BEARING", ["bearing"]),
    ("ROLL_CHANGE", ["roll change"]),
]


def _cause(text):
    value = (text or "").strip().lower()
    if not value:
        return "UNSPECIFIED"
    for label, needles in CAUSE_RULES:
        if any(n in value for n in needles):
            return label
    return "OTHER"


def _avg(values):
    vals = [float(v) for v in values if v is not None]
    return round(mean(vals), 2) if vals else None


def _med(values):
    vals = [float(v) for v in values if v is not None]
    return round(median(vals), 2) if vals else None


def _live_events(db: Session, line: str, position: int):
    rows = (
        db.query(StandCampaignEvent, StandInstallation)
        .join(StandInstallation, StandCampaignEvent.installation_id == StandInstallation.id)
        .join(Position, StandInstallation.position_id == Position.id)
        .join(Line, Position.line_id == Line.id)
        .filter(Line.name == line, Position.position_number == position)
        .order_by(StandCampaignEvent.event_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": event.id,
            "stand_id": event.stand_id,
            "category": event.category,
            "event_type": event.event_type,
            "severity": event.severity,
            "component_name": event.component_name,
            "duration_minutes": event.duration_minutes,
            "description": event.description,
            "action_taken": event.action_taken,
            "event_at": event.event_at.isoformat() if event.event_at else None,
            "recorded_by": event.recorded_by,
            "campaign_installed_at": installation.installed_at.isoformat() if installation.installed_at else None,
            "campaign_removed_at": installation.removed_at.isoformat() if installation.removed_at else None,
        }
        for event, installation in rows
    ]


@router.get("/position")
def investigate_position(
    line: str = Query(..., pattern="^W[123]$"),
    position: int = Query(..., ge=1, le=10),
    db: Session = Depends(get_db),
):
    live_events = _live_events(db, line, position)
    event_types = Counter((e["event_type"] or "UNSPECIFIED").strip().upper() for e in live_events)
    event_components = Counter((e["component_name"] or "").strip() for e in live_events if e.get("component_name"))
    stoppages = sum(1 for e in live_events if e["severity"] == "STOPPAGE")
    downtime_minutes = round(sum(float(e.get("duration_minutes") or 0) for e in live_events), 1)

    campaigns = db.query(HistoricalCampaign).filter(
        HistoricalCampaign.line_name == line,
        HistoricalCampaign.position_number == position,
        HistoricalCampaign.life_days.isnot(None),
    ).order_by(HistoricalCampaign.installed_date.desc()).all()
    valid = [c for c in campaigns if c.life_days is not None and c.life_days > 0]
    event_summary = {
        "count": len(live_events),
        "stoppages": stoppages,
        "downtime_minutes": downtime_minutes,
        "top_types": [{"event": k, "count": v} for k, v in event_types.most_common(8)],
        "top_components": [{"component": k, "count": v} for k, v in event_components.most_common(8)],
    }

    if not valid:
        return {
            "line": line,
            "position": position,
            "campaigns": 0,
            "message": "No measurable historical campaigns imported for this position yet.",
            "timeline": [],
            "causes": [],
            "stand_codes": [],
            "nearby_spares": [],
            "process": [],
            "live_events": live_events,
            "event_summary": event_summary,
        }

    lives = [c.life_days for c in valid]
    med = median(lives)
    early_threshold = med * 0.6

    timeline = []
    stand_lives = defaultdict(list)
    cause_counts = Counter()
    early_windows = []
    for c in valid:
        stand_lives[c.stand_code].append(c.life_days)
        cause = _cause(c.removal_reason)
        if cause != "UNSPECIFIED":
            cause_counts[cause] += 1
        is_early = c.life_days <= early_threshold
        if is_early and c.installed_date and c.removed_date:
            early_windows.append((c.installed_date, c.removed_date))
        timeline.append({
            "stand": c.stand_code,
            "installed": c.installed_date.isoformat() if c.installed_date else None,
            "removed": c.removed_date.isoformat() if c.removed_date else None,
            "life_days": c.life_days,
            "reason": c.removal_reason,
            "cause": cause,
            "early": is_early,
            "confidence": c.confidence,
            "inferred": c.inferred,
            "source_file": c.source_file,
        })

    stand_codes = []
    for code, vals in stand_lives.items():
        stand_codes.append({
            "stand": code,
            "campaigns": len(vals),
            "avg_days": _avg(vals),
            "median_days": _med(vals),
            "early_campaigns": sum(1 for v in vals if v <= early_threshold),
        })
    stand_codes.sort(key=lambda x: (x["avg_days"] if x["avg_days"] is not None else 999999, -x["campaigns"]))

    spare_rows = db.query(HistoricalSpareUsage).all()
    nearby_spares = defaultdict(float)
    matched_spare_days = set()
    for s in spare_rows:
        for start, end in early_windows:
            if start - timedelta(days=2) <= s.usage_date <= end + timedelta(days=2):
                nearby_spares[s.spare_name] += float(s.quantity or 0)
                matched_spare_days.add(s.usage_date)
                break
    nearby_spares = sorted(
        ({"spare": k, "quantity": round(v, 2)} for k, v in nearby_spares.items()),
        key=lambda x: x["quantity"], reverse=True,
    )[:15]

    all_process = db.query(ProcessObservation).filter(ProcessObservation.line_name == line).all()
    early_process = []
    for o in all_process:
        if any(start <= o.observation_date <= end for start, end in early_windows):
            early_process.append(o)

    process_results = []
    for field, label in (("casting_speed", "Casting speed"), ("emulsion_temp", "Emulsion temperature")):
        all_vals = [getattr(o, field) for o in all_process if getattr(o, field) is not None]
        early_vals = [getattr(o, field) for o in early_process if getattr(o, field) is not None]
        if all_vals:
            overall = mean(all_vals)
            early = mean(early_vals) if early_vals else None
            delta = ((early - overall) / overall * 100) if early is not None and overall else None
            process_results.append({
                "parameter": label,
                "overall_avg": round(overall, 2),
                "early_avg": round(early, 2) if early is not None else None,
                "difference_pct": round(delta, 1) if delta is not None else None,
                "overall_samples": len(all_vals),
                "early_samples": len(early_vals),
            })

    return {
        "line": line,
        "position": position,
        "campaigns": len(valid),
        "avg_days": _avg(lives),
        "median_days": _med(lives),
        "min_days": round(min(lives), 2),
        "max_days": round(max(lives), 2),
        "early_threshold_days": round(early_threshold, 2),
        "early_campaigns": sum(1 for v in lives if v <= early_threshold),
        "causes": [{"cause": k, "count": v} for k, v in cause_counts.most_common(12)],
        "stand_codes": stand_codes,
        "timeline": timeline[:80],
        "nearby_spares": nearby_spares,
        "spare_match_days": len(matched_spare_days),
        "process": process_results,
        "live_events": live_events,
        "event_summary": event_summary,
        "method_note": "Live campaign events are exact records linked to stand installations. Imported stand history, spare usage and process parameters remain separate evidence streams. Date alignment is screening evidence, not confirmed root cause.",
    }
