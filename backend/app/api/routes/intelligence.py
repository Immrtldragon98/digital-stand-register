from collections import Counter, defaultdict
from statistics import mean, median
from typing import Literal
from app.services.life_insight_service import dedupe_completed_campaigns, completed_comparisons

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.services.intelligence_answer_service import answer_from_evidence, question_scope
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.line import Line
from app.services.evidence_service import bounded_rows, merge_intervals, in_intervals
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


def _safe_avg(values):
    values = [float(v) for v in values if v is not None]
    return round(mean(values), 2) if values else None


def _safe_median(values):
    values = [float(v) for v in values if v is not None]
    return round(median(values), 2) if values else None


MIN_COMPARISON_SAMPLES = 3


def completed_snapshot_campaigns(campaigns):
    return dedupe_completed_campaigns(campaigns)[0]


def position_screening(campaigns):
    """Adapt the shared comparison calculation to the existing summary contract."""
    _, positions = completed_comparisons(campaigns)
    return [{**row, "vs_position_baseline_pct": row["vs_peer_pct"],
             "eligible_for_comparison": row["evidence"] == "SUFFICIENT",
             "evidence_strength": "LIMITED" if row["evidence"] != "SUFFICIENT" else "PRELIMINARY",
             "life_basis": row["basis"]} for row in positions]


@router.get("/summary")
def intelligence_summary(db: Session = Depends(get_db)):
    campaigns, campaigns_truncated = bounded_rows(db.query(HistoricalCampaign).order_by(HistoricalCampaign.installed_date.desc(), HistoricalCampaign.id.desc()))
    spares, spares_truncated = bounded_rows(db.query(HistoricalSpareUsage).order_by(HistoricalSpareUsage.usage_date.desc(), HistoricalSpareUsage.id.desc()))
    process, process_truncated = bounded_rows(db.query(ProcessObservation).order_by(ProcessObservation.observation_date.desc(), ProcessObservation.id.desc()))

    # Open installations are right-censored and cannot enter completed-life averages.
    valid, history_exclusions = dedupe_completed_campaigns(campaigns)
    line_names = sorted({row.name for row in db.query(Line).limit(1000).all()} | {row.line_name for row in campaigns} | {row.line_name for row in process})
    line_stats = []
    for line in line_names:
        lv = [c.life_days for c in valid if c.line_name == line]
        line_stats.append({"line": line, "campaigns": len(lv), "avg_days": _safe_avg(lv), "median_days": _safe_median(lv),
            "life_basis": "INFERRED_SNAPSHOT_ELAPSED_DAYS", "comparison_note": "Mixed position summary only; do not rank whole lines from this value."})
    position_stats = position_screening(valid)
    weak_positions = sorted((p for p in position_stats if p["eligible_for_comparison"]), key=lambda p: p["vs_position_baseline_pct"])

    cause_counts = Counter(_cause(c.removal_reason) for c in valid if c.removal_reason)
    cause_pareto = [{"cause": k, "count": v} for k, v in cause_counts.most_common(12)]

    stand_stats, _ = completed_comparisons(valid)
    repeat_low_life = [{**row, "vs_peer_median_pct": row["vs_peer_pct"],
        "life_basis": row["basis"], "evidence_strength": "PRELIMINARY"}
        for row in stand_stats if row["evidence"] == "SUFFICIENT" and row["vs_peer_pct"] < 0]
    repeat_low_life.sort(key=lambda row: row["vs_peer_median_pct"])

    spare_totals = defaultdict(float)
    for s in spares:
        spare_totals[s.spare_name] += float(s.quantity or 0)
    top_spares = sorted(
        ({"spare": k, "quantity": round(v, 2)} for k, v in spare_totals.items()),
        key=lambda x: x["quantity"], reverse=True
    )[:12]

    process_by_line = defaultdict(list)
    for p in process:
        process_by_line[p.line_name].append(p)
    process_screen = []
    for line in line_names:
        lc = [c for c in valid if c.line_name == line]
        if not lc or not process_by_line[line]:
            continue
        med = median([c.life_days for c in lc])
        early_intervals = merge_intervals((c.installed_date, c.removed_date) for c in lc
            if c.life_days <= med * 0.6 and c.installed_date and c.removed_date)
        all_obs = process_by_line[line]
        early_obs = [o for o in all_obs if in_intervals(o.observation_date, early_intervals)]
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
        "history_exclusions": history_exclusions,
        "life_basis": "INFERRED_SNAPSHOT_ELAPSED_DAYS",
        "history_truncated": {"campaigns": campaigns_truncated, "spares": spares_truncated, "process": process_truncated},
        "data": {"campaigns": len(valid), "spare_usage_rows": len(spares), "process_observations": len(process)},
        "line_stats": line_stats,
        "weak_positions": weak_positions[:10],
        "position_comparisons": position_stats,
        "comparison_min_samples": MIN_COMPARISON_SAMPLES,
        "cause_pareto": cause_pareto,
        "repeat_low_life": repeat_low_life[:12],
        "top_spares": top_spares,
        "process_screen": process_screen,
        "method_note": "Life is inferred snapshot elapsed days, not measured mill runtime. Only completed campaigns enter averages; duplicate imports and ongoing campaigns are excluded. Position screening uses medians against other lines at the same position, with at least 3 campaigns on each side, and does not establish a failure cause or statistical significance. Analytics uses the latest 20,000 rows per stream; truncation flags identify excluded history. Historical campaigns reconstructed from daily snapshots are inferred. Zero-day changeover ambiguity is excluded from life baselines. Process comparisons are correlations for engineering screening, not confirmed causes."
    }


class AssistantScope(BaseModel):
    line: str = Field(min_length=1, max_length=50)
    position: int | None = Field(default=None, ge=1, le=10)
    topic: Literal["LONGEST_CURRENT", "COMPLETED_STAND_COMPARISON", "WEAK_POSITIONS", "INVESTIGATION", "RUNTIME_STATUS", "CURRENT_STOCK", "SPARE_LIFE", "MAINTENANCE_VALUE", "HELP", "SPARE_USAGE"] | None = None


class IntelligenceQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    context: AssistantScope | None = None


@router.post("/ask")
def ask_intelligence(payload: IntelligenceQuestion, db: Session = Depends(get_db)):
    # Read-only analytics remains available if external model quota or connectivity fails.
    from app.services.life_insight_service import LifeInsightService
    insights = LifeInsightService(db).summary()
    history = intelligence_summary(db)
    from app.services.maintenance_assistant_service import resolve_scope, enhanced_answer
    query, scope = resolve_scope(payload.question.strip(), payload.context.model_dump() if payload.context else None, insights)
    line, position = (scope['line'], scope['position']) if scope else (None, None)
    if line and position is not None:
        from app.api.routes.investigation import investigate_position
        history['position_investigation'] = investigate_position(line, position, db)
    import re
    from app.models.inventory_item import InventoryItem
    from app.services.spare_life_service import life_summaries, life_summary
    from app.services.plant_value_service import PlantValueService
    items = None
    if re.search(r'STOCK|SPARE|COMPONENT|BEARING|SEAL|SLEEVE|BALANCE|SHORTAGE|AVAILABLE|AVAILABILITY|QUANTITY|QUANTITIES|HOW MANY|DO WE HAVE|IN STORE', query.upper()):
        summaries = life_summaries(db)
        items = [{'id': row.id, 'name': row.name, 'quantity': row.quantity, 'minimum': row.minimum_quantity,
                  **life_summary(row, summaries)} for row in db.query(InventoryItem).filter(InventoryItem.is_active.is_(True)).order_by(InventoryItem.name).all()]
    plant = None
    if re.search(r'UNKNOWN|RUNTIME|RUNNING|STOPPED|STATE|PREPARATION|INVESTIGATION (TIME|EFFORT)|SAVINGS|MAINTENANCE VALUE', query.upper()):
        plant = PlantValueService(db).summary()
    return enhanced_answer(query, insights, history, scope=scope, plant=plant, items=items)
