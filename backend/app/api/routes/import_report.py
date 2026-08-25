import re
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth.dependencies import require_operator
from app.models.user import User

router = APIRouter()

class ReportInput(BaseModel):
    text: str


def _value(text: str, label: str):
    m = re.search(rf"(?im)^\s*{label}\s*[:-]\s*(.+?)\s*$", text)
    return m.group(1).strip() if m else None


def _stand_list(text: str, heading: str):
    m = re.search(rf"(?is){heading}\s*:?(.*?)(?=\n\s*(?:READY|HYDROTEST|GAUGING|PENDING|YET TO READY|ENTRY GUIDES?|STAND CHANGE)\s*:|$)", text)
    if not m:
        return []
    return re.findall(r"\b(?:10|[1-9])(?:\.[1-9]|[A-E])\b", m.group(1), flags=re.I)

@router.post("/analyse")
def analyse_report(payload: ReportInput, user: User = Depends(require_operator)):
    text = payload.text.strip()
    actions = []
    warnings = []

    removed = _value(text, r"Stand\s*Remove")
    fixed = _value(text, r"Stand\s*Fixed")
    line = _value(text, r"Line")
    if not line:
        wrm = re.search(r"(?i)WRM\s*#?\s*([123])", text)
        line = f"W{wrm.group(1)}" if wrm else None
    if removed and fixed:
        pos = re.match(r"(10|[1-9])", fixed)
        actions.append({
            "type": "STAND_CHANGE", "line": line, "position": int(pos.group(1)) if pos else None,
            "stand_removed": removed, "stand_fixed": fixed,
            "done_by": _value(text, r"(?:Changed By|S\.I\.)"),
            "reason": _value(text, r"Reason"), "date": _value(text, r"Date"),
            "time": _value(text, r"Time"), "shift": _value(text, r"Shift")
        })

    for heading, status in [("READY", "READY"), ("HYDROTEST", "HYDROTEST"), ("GAUGING", "GAUGING"), ("PENDING", "PENDING"), ("YET TO READY", "YET_TO_READY")]:
        for code in _stand_list(text, heading):
            actions.append({"type": "STAND_STATUS", "stand": code.upper(), "status": status})

    if not actions:
        warnings.append("No supported stand operation was confidently detected. Use the team template or review the message.")

    return {
        "provider": "template-parser",
        "analysed_by": user.username,
        "actions": actions,
        "warnings": warnings,
        "message": "Preview only. No plant data has been changed."
    }
