import re
from collections import Counter, defaultdict
from statistics import mean, median

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.reliability_history import HistoricalCampaign, HistoricalSpareUsage, ProcessObservation

router = APIRouter()

CAUSE_RULES = [
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
    ("ROLL_CHANGE", ["roll change", "roll"]),
]


def _cause(text):
    value = (text or "").strip().lower()
    if not value:
        return "UNSPECIFIED"
    for label, needles in CAUSE_RULES:
        if any(n in value for n in needles):
            return label
    return "OTHER"


def _safe_avg(values):
    values = [float(v) for v in values if v is not None]
    return round(mean(values), 2) if values else None


def _safe_median(values):
    values = [float(v) for v in values if v is not None]
    return round(median(values), 2) if values else None


@router.get("/summary")
def intelligence_summary(db: Session = Depends(get_db)):
    campaigns = db.query(HistoricalCampaign).filter(HistoricalCampaign.life_days.isnot(None)).all()
    spares = db.query(HistoricalSpareUsage).all()
    process = db.query(ProcessObservation).all()

    valid = [c for c in campaigns if c.life_days is not None and c.life_days >= 0]
    line_stats = []
    position_stats = []
    for line in ("W1", "W2", "W3"):
        lv = [c.life_days for c in valid if c.line_name == line]
        line_stats.append({"line": line, "campaigns": len(lv), "avg_days": _safe_avg(lv), "median_days": _safe_median(lv)})
        for pos in range(1, 11):
            pv = [c.life_days for c in valid if c.line_name == line and c.position_number == pos]
            if pv:
                position_stats.append({
                    "line": line, "position": pos, "campaigns": len(pv),
                    "avg_days": _safe_avg(pv), "median_days": _safe_median(pv),
                    "min_days": round(min(pv), 2), "max_days": round(max(pv), 2),
                })

    # Weak positions are relative to the same position across all lines, not an arbitrary plant target.
    pos_baseline = {}
    for pos in range(1, 11):
        vals = [c.life_days for c in valid if c.position_number == pos]
        pos_baseline[pos] = mean(vals) if vals else None
    weak_positions = []
    for p in position_stats:
        baseline = pos_baseline.get(p["position"])
        if baseline and p["avg_days"] is not None:
            delta = ((p["avg_days"] - baseline) / baseline) * 100
            weak_positions.append({**p, "vs_position_baseline_pct": round(delta, 1)})
    weak_positions.sort(key=lambda x: x["vs_position_baseline_pct"])

    cause_counts = Counter(_cause(c.removal_reason) for c in valid if c.removal_reason)
    cause_pareto = [{"cause": k, "count": v} for k, v in cause_counts.most_common(12)]

    # Stand-code repeat low-life view. Require at least 3 completed historical campaigns.
    by_stand = defaultdict(list)
    for c in valid:
        by_stand[c.stand_code].append(c.life_days)
    repeat_low_life = []
    for code, vals in by_stand.items():
        if len(vals) < 3:
            continue
        repeat_low_life.append({"stand": code, "campaigns": len(vals), "avg_days": _safe_avg(vals), "median_days": _safe_median(vals)})
    repeat_low_life.sort(key=lambda x: (x["avg_days"] if x["avg_days"] is not None else 999999, -x["campaigns"]))

    spare_totals = defaultdict(float)
    for s in spares:
        spare_totals[s.spare_name] += float(s.quantity or 0)
    top_spares = sorted(
        ({"spare": k, "quantity": round(v, 2)} for k, v in spare_totals.items()),
        key=lambda x: x["quantity"], reverse=True
    )[:12]

    # Process comparison: compare observations on dates overlapping short campaigns with overall line average.
    # This is only a screening correlation, never a root-cause claim.
    process_by_line = defaultdict(list)
    for p in process:
        process_by_line[p.line_name].append(p)
    process_screen = []
    for line in ("W1", "W2", "W3"):
        lc = [c for c in valid if c.line_name == line]
        if not lc or not process_by_line[line]:
            continue
        med = median([c.life_days for c in lc])
        early_dates = set()
        for c in lc:
            if c.life_days <= med * 0.6 and c.installed_date and c.removed_date:
                d = c.installed_date
                while d <= c.removed_date:
                    early_dates.add(d)
                    from datetime import timedelta
                    d += timedelta(days=1)
        all_obs = process_by_line[line]
        early_obs = [o for o in all_obs if o.observation_date in early_dates]
        for field, label in (("casting_speed", "Casting speed"), ("emulsion_temp", "Emulsion temperature")):
            all_vals = [getattr(o, field) for o in all_obs if getattr(o, field) is not None]
            early_vals = [getattr(o, field) for o in early_obs if getattr(o, field) is not None]
            if len(all_vals) >= 5 and len(early_vals) >= 2:
                a = mean(all_vals); e = mean(early_vals)
                delta = ((e - a) / a * 100) if a else None
                process_screen.append({
                    "line": line, "parameter": label, "overall_avg": round(a, 2),
                    "early_campaign_avg": round(e, 2), "difference_pct": round(delta, 1) if delta is not None else None,
                    "early_samples": len(early_vals), "note": "Screening correlation only"
                })

    return {
        "data": {"campaigns": len(valid), "spare_usage_rows": len(spares), "process_observations": len(process)},
        "line_stats": line_stats,
        "weak_positions": weak_positions[:10],
        "cause_pareto": cause_pareto,
        "repeat_low_life": repeat_low_life[:12],
        "top_spares": top_spares,
        "process_screen": process_screen,
        "method_note": "Historical campaigns reconstructed from daily snapshots are inferred. Process comparisons are correlations for engineering screening, not confirmed causes."
    }
