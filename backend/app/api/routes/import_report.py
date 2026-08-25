import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import require_operator
from app.database.session import get_db
from app.models.enums import StatusEnum
from app.models.line import Line
from app.models.stand_asset import StandAsset
from app.models.stand_position import Position
from app.models.user import User
from app.schemas.operation import ChangeStandSchema
from app.services.operation_service import OperationService, PREPARATION_FLOW

router = APIRouter()
logger = logging.getLogger(__name__)


class ReportInput(BaseModel):
    text: str


class ValidateInput(BaseModel):
    actions: list[dict]


class ConfirmInput(BaseModel):
    actions: list[dict]


SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["STAND_CHANGE", "STAND_STATUS", "ENTRY_GUIDE_SUMMARY", "ENTRY_GUIDE_CHANGE"]},
                    "stand": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"]},
                    "line": {"type": ["string", "null"]},
                    "position": {"type": ["integer", "null"]},
                    "stand_removed": {"type": ["string", "null"]},
                    "stand_fixed": {"type": ["string", "null"]},
                    "done_by": {"type": ["string", "null"]},
                    "reason": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                    "time": {"type": ["string", "null"]},
                    "shift": {"type": ["string", "null"]},
                    "guide_condition": {"type": ["string", "null"]},
                    "old_ready": {"type": ["integer", "null"]},
                    "new_ready": {"type": ["integer", "null"]},
                    "confidence": {"type": "number"},
                },
                "required": ["type", "confidence"],
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["actions", "warnings"],
}

PROMPT = '''You are the Digital Stand Register report interpreter for a wire rod mill.
Extract operations only; never invent missing facts.
Vocabulary: WRM#1=W1, WRM#2=W2, WRM#3=W3. HT=HYDROTEST. Gauge/gauging=GAUGING.
Stand workflow: YET_TO_READY -> PENDING -> GAUGING -> HYDROTEST -> READY -> RUNNING.
Only stands at positions 2,4,6,8,10 use entry guides.
For a stand change extract old/new stand, line, position, people, reason, date/time/shift when present.
For readiness reports create STAND_STATUS actions. If text says a test is pending, do NOT claim it is completed; add a warning if exact current stage is unclear.
For entry guide stock summaries create ENTRY_GUIDE_SUMMARY with position and old_ready/new_ready counts.
For entry guide changes create ENTRY_GUIDE_CHANGE and preserve New/Old condition. A line such as "Entry guide - 8(old) and 10(new)" means the report mentions those guide positions/conditions, but if installation/removal is not explicit keep confidence moderate and add a warning.
Use confidence 0..1. Ambiguous facts belong in warnings, not guesses.
REPORT:\n'''

_WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _value(text, label):
    m = re.search(rf"(?im)^\s*{label}\s*[:-]\s*(.+?)\s*$", text)
    return m.group(1).strip() if m else None


def _stand_list(text, heading):
    m = re.search(rf"(?is){heading}\s*:?(.*?)(?=\n\s*(?:READY|HYDROTEST|GAUGING|PENDING|YET TO READY|ENTRY GUIDES?|STAND CHANGE)\s*:|$)", text)
    return re.findall(r"\b(?:10|[1-9])(?:\.[1-9]|[A-E])\b", m.group(1), flags=re.I) if m else []


def _count_word(value):
    if not value:
        return 0
    value = value.strip().lower()
    if value.isdigit():
        return int(value)
    return _WORD_NUMBERS.get(value, 0)


def _entry_guide_actions(text, line, done_by, reason, date, shift):
    actions = []
    warnings = []

    # Stock/readiness wording, e.g. "Entry guide for stand 10 :- ready two old set and one new."
    summary_re = re.compile(
        r"(?i)entry\s*guide\s*for\s*stand\s*(10|[2468])\s*[:-]?\s*ready\s*(?:(\d+|one|two|three|four|five|six)\s*old(?:\s*set)?s?)?(?:\s*(?:and|,)?\s*(\d+|one|two|three|four|five|six)\s*new(?:\s*set)?s?)?"
    )
    for m in summary_re.finditer(text):
        actions.append({
            "type": "ENTRY_GUIDE_SUMMARY",
            "line": line,
            "position": int(m.group(1)),
            "old_ready": _count_word(m.group(2)),
            "new_ready": _count_word(m.group(3)),
            "done_by": done_by,
            "date": date,
            "shift": shift,
            "confidence": 0.95,
        })

    # Short shift wording, e.g. "Entry guide - 8(old) and 10(Old)".
    short = re.search(r"(?im)^\s*entry\s*guide\s*[-:]\s*(.+)$", text)
    if short:
        for pos, condition in re.findall(r"\b(10|[2468])\s*\(\s*(old|new)\s*\)", short.group(1), flags=re.I):
            actions.append({
                "type": "ENTRY_GUIDE_CHANGE",
                "line": line,
                "position": int(pos),
                "guide_condition": condition.upper(),
                "done_by": done_by,
                "reason": reason,
                "date": date,
                "shift": shift,
                "confidence": 0.78,
            })
        if re.search(r"\b(10|[2468])\s*\(\s*(old|new)\s*\)", short.group(1), flags=re.I):
            warnings.append("Entry-guide positions were detected, but the message does not explicitly say whether each guide was installed, removed or only inspected. Review before updating.")

    return actions, warnings


def template_parse(text):
    actions = []
    warnings = []
    removed = _value(text, r"Stand\s*Remove")
    fixed = _value(text, r"Stand\s*Fixed")
    line = _value(text, r"Line")
    if not line:
        wrm = re.search(r"(?i)WRM\s*#?\s*([123])", text)
        line = f"W{wrm.group(1)}" if wrm else None
    done_by = _value(text, r"(?:Changed By|S\.I\.)")
    reason = _value(text, r"Reason")
    date = _value(text, r"Date")
    if not date:
        date_line = re.search(r"(?m)^\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*$", text)
        date = date_line.group(1) if date_line else None
    shift = _value(text, r"Shift")

    if removed and fixed:
        pos = re.match(r"(10|[1-9])", fixed)
        actions.append({
            "type": "STAND_CHANGE",
            "line": line,
            "position": int(pos.group(1)) if pos else None,
            "stand_removed": removed.strip().upper(),
            "stand_fixed": fixed.strip().upper(),
            "done_by": done_by,
            "reason": reason,
            "date": date,
            "time": _value(text, r"Time"),
            "shift": shift,
            "confidence": 0.95,
        })

    for heading, status in [("READY", "READY"), ("HYDROTEST", "HYDROTEST"), ("GAUGING", "GAUGING"), ("PENDING", "PENDING"), ("YET TO READY", "YET_TO_READY")]:
        for code in _stand_list(text, heading):
            actions.append({"type": "STAND_STATUS", "stand": code.upper(), "status": status, "done_by": done_by, "confidence": 0.95})

    guide_actions, guide_warnings = _entry_guide_actions(text, line, done_by, reason, date, shift)
    actions.extend(guide_actions)
    warnings.extend(guide_warnings)

    if not actions:
        warnings.append("No supported operation confidently detected by fallback parser.")
    return {"actions": actions, "warnings": warnings}


def _gemini_request(key, model, text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent"
    body = {
        "contents": [{"parts": [{"text": PROMPT + text}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "responseJsonSchema": SCHEMA},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="ignore")[:1200].replace("\n", " ").replace("\r", " ")
        logger.warning("Gemini model=%s HTTP %s: %s", model, exc.code, body_text)
        raise RuntimeError(f"Gemini {model} HTTP {exc.code}") from exc
    result_text = raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(result_text)


def gemini_parse(text):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    configured = (os.getenv("GEMINI_MODEL") or "").strip()
    candidates = []
    for model in (configured, "gemini-2.5-flash-lite", "gemini-2.5-flash"):
        if model and model not in candidates:
            candidates.append(model)

    errors = []
    for model in candidates:
        try:
            parsed = _gemini_request(key, model, text)
            parsed["model"] = model
            return parsed
        except RuntimeError as exc:
            errors.append(str(exc))
            # A 404 often means a model alias is unavailable to this API project; try another stable free-tier model.
            if "HTTP 404" in str(exc):
                continue
            raise
    raise RuntimeError("; ".join(errors) or "Gemini request failed")


def _parse_changed_at(action: dict):
    date = (action.get("date") or "").strip()
    time = (action.get("time") or "").strip()
    if not date:
        return None, None
    if not time:
        return None, "Time is required for a dated stand change."
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%y %H:%M", "%d-%m-%Y %H:%M", "%d-%m-%y %H:%M"):
        try:
            return datetime.strptime(f"{date} {time}", fmt), None
        except ValueError:
            pass
    return None, "Date/time format not recognised. Use DD/MM/YYYY and HH:MM."


def _find_position(db: Session, line_name: str | None, position_number: int | None):
    if not line_name or not position_number:
        return None
    line_name = line_name.upper().replace("WRM#", "W").replace("WRM", "W")
    return db.query(Position).join(Line).filter(Line.name == line_name, Position.position_number == position_number).first()


def validate_action(db: Session, action: dict):
    kind = action.get("type")
    confidence = float(action.get("confidence") or 0)
    if confidence and confidence < 0.75:
        return "REVIEW", "AI confidence is low. Check this item before updating."

    if kind == "STAND_STATUS":
        code = (action.get("stand") or "").strip().upper()
        target_raw = (action.get("status") or "").strip().upper()
        stand = db.query(StandAsset).filter(StandAsset.code == code).first()
        if not stand:
            return "CONFLICT", f"Stand {code or '?'} does not exist in DSR."
        try:
            target = StatusEnum(target_raw)
        except ValueError:
            return "CONFLICT", f"Unknown status {target_raw or '?'} ."
        if stand.current_status == StatusEnum.INSTALLED or stand.current_position_id is not None:
            return "CONFLICT", f"{code} is currently running and cannot be marked {target.value}."
        current = stand.current_status
        if current == target:
            return "SAFE", f"{code} is already {target.value}; no change needed."
        normalized_current = StatusEnum.PENDING if current == StatusEnum.INP else current
        if normalized_current not in PREPARATION_FLOW or target not in PREPARATION_FLOW:
            return "CONFLICT", f"{code} is not in the preparation workflow."
        ci = PREPARATION_FLOW.index(normalized_current)
        ti = PREPARATION_FLOW.index(target)
        if ti == ci + 1 or (target == StatusEnum.PENDING and normalized_current != StatusEnum.YET_TO_READY):
            if target in {StatusEnum.GAUGING, StatusEnum.HYDROTEST, StatusEnum.READY} and not (action.get("done_by") or "").strip():
                return "REVIEW", f"{target.value} needs the name of the person who completed it."
            return "SAFE", f"{code}: {normalized_current.value} → {target.value}."
        return "REVIEW", f"{code} is {normalized_current.value}; report says {target.value}. Intermediate workflow steps are missing."

    if kind == "STAND_CHANGE":
        old_code = (action.get("stand_removed") or "").strip().upper()
        new_code = (action.get("stand_fixed") or "").strip().upper()
        old = db.query(StandAsset).filter(StandAsset.code == old_code).first()
        new = db.query(StandAsset).filter(StandAsset.code == new_code).first()
        if not old or not new:
            missing = old_code if not old else new_code
            return "CONFLICT", f"Stand {missing or '?'} does not exist in DSR."
        position = _find_position(db, action.get("line"), action.get("position"))
        if not position:
            return "CONFLICT", "Line / position could not be matched to DSR."
        if old.current_position_id != position.id or old.current_status != StatusEnum.INSTALLED:
            return "CONFLICT", f"{old_code} is not the running stand at {action.get('line')} position {action.get('position')}."
        if new.current_status != StatusEnum.READY or new.current_position_id is not None:
            return "CONFLICT", f"Replacement {new_code} is not available in Ready."
        if not (action.get("done_by") or "").strip() or not (action.get("reason") or "").strip():
            return "REVIEW", "Stand change needs Changed By and Reason."
        _, time_error = _parse_changed_at(action)
        if time_error:
            return "REVIEW", time_error
        return "SAFE", f"{action.get('line')} position {action.get('position')}: {old_code} → {new_code}."

    if kind in {"ENTRY_GUIDE_SUMMARY", "ENTRY_GUIDE_CHANGE"}:
        position = action.get("position")
        if position not in {2, 4, 6, 8, 10}:
            return "CONFLICT", "Entry guides are only valid for positions 2, 4, 6, 8 and 10."
        return "REVIEW", "Entry-guide information was understood. Review it before we enable automatic guide updates."

    return "REVIEW", "Unsupported action type."


@router.post("/analyse")
def analyse_report(payload: ReportInput, user: User = Depends(require_operator)):
    text = payload.text.strip()
    provider = "gemini"
    ai_error = None
    model = None
    try:
        parsed = gemini_parse(text)
        model = parsed.pop("model", None)
    except Exception as exc:
        ai_error = str(exc)
        logger.warning("Gemini unavailable; fallback parser used: %s", ai_error)
        provider = "template-parser"
        parsed = template_parse(text)
        parsed["warnings"].append(f"AI unavailable ({ai_error}); used free template parser instead.")
    return {"provider": provider, "model": model, "analysed_by": user.username, "actions": parsed.get("actions", []), "warnings": parsed.get("warnings", []), "message": "Preview only. No plant data has been changed."}


@router.post("/validate")
def validate_report(payload: ValidateInput, db: Session = Depends(get_db), user: User = Depends(require_operator)):
    items = []
    counts = {"SAFE": 0, "REVIEW": 0, "CONFLICT": 0}
    for index, action in enumerate(payload.actions):
        state, message = validate_action(db, action)
        counts[state] += 1
        items.append({"index": index, "state": state, "message": message, "action": action})
    return {"items": items, "counts": counts, "validated_by": user.username}


@router.post("/confirm")
def confirm_report(payload: ConfirmInput, db: Session = Depends(get_db), user: User = Depends(require_operator)):
    service = OperationService(db)
    results = []
    for action in payload.actions:
        state, message = validate_action(db, action)
        if state != "SAFE":
            results.append({"action": action, "status": "SKIPPED", "message": message})
            continue
        try:
            if action.get("type") == "STAND_STATUS":
                stand = db.query(StandAsset).filter(StandAsset.code == (action.get("stand") or "").strip().upper()).first()
                target = StatusEnum((action.get("status") or "").strip().upper())
                if stand and stand.current_status == target:
                    results.append({"action": action, "status": "NO_CHANGE", "message": f"{stand.code} already {target.value}."})
                    continue
                done_by = (action.get("done_by") or user.username).strip()
                result = service.update_preparation_status(action["stand"].strip().upper(), target, user.id, done_by, "Imported from shift report")
                results.append({"action": action, "status": "UPDATED", "result": result})
            elif action.get("type") == "STAND_CHANGE":
                position = _find_position(db, action.get("line"), action.get("position"))
                changed_at, _ = _parse_changed_at(action)
                change = ChangeStandSchema(
                    position_id=position.id,
                    removed_stand_code=action["stand_removed"].strip().upper(),
                    installed_stand_code=action["stand_fixed"].strip().upper(),
                    changed_by=action["done_by"].strip(),
                    reason=action["reason"].strip(),
                    changed_at=changed_at,
                    notes="Imported from shift report",
                )
                result = service.change_stand(change, user.id)
                results.append({"action": action, "status": "UPDATED", "result": result})
            else:
                results.append({"action": action, "status": "SKIPPED", "message": "Automatic update not supported for this action."})
        except HTTPException as exc:
            db.rollback()
            results.append({"action": action, "status": "FAILED", "message": str(exc.detail)})
    updated = sum(1 for item in results if item["status"] == "UPDATED")
    return {"updated": updated, "results": results, "confirmed_by": user.username}
