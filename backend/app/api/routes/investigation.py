from collections import Counter, defaultdict
from datetime import timedelta
from statistics import mean, median

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.reliability_history import HistoricalCampaign, HistoricalSpareUsage, ProcessObservation

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


@router.get("/position")
def investigate_position(
    line: str = Query(..., pattern="^W[123]$"),
    position: int = Query(..., ge=1, le=10),
    db: Session = Depends(get_db),
):
    campaigns = db.query(HistoricalCampaign).filter(
        HistoricalCampaign.line_name == line,
        HistoricalCampaign.position_number == position,
        HistoricalCampaign.life_days.isnot(None),
    ).order_by(HistoricalCampaign.installed_date.desc()).all()
    valid = [c for c in campaigns if c.life_days is not None and c.life_days > 0]
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

    # Spare history is independent from stand history. We only screen consumption within ±2 days of early removals.
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

    # Process parameters remain a separate evidence stream. Compare observations during early campaign windows with all line observations.
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
        "method_note": "Stand history, spare usage and process parameters remain separate datasets. The page aligns them by date only for engineering screening. Associations are not confirmed root causes.",
    }
