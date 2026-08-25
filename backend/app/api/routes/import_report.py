import json
import os
import re
import urllib.request
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth.dependencies import require_operator
from app.models.user import User

router = APIRouter()

class ReportInput(BaseModel):
    text: str

SCHEMA = {
    "type":"object",
    "properties":{
        "actions":{"type":"array","items":{"type":"object","properties":{
            "type":{"type":"string","enum":["STAND_CHANGE","STAND_STATUS","ENTRY_GUIDE_SUMMARY","ENTRY_GUIDE_CHANGE"]},
            "stand":{"type":["string","null"]},"status":{"type":["string","null"]},
            "line":{"type":["string","null"]},"position":{"type":["integer","null"]},
            "stand_removed":{"type":["string","null"]},"stand_fixed":{"type":["string","null"]},
            "done_by":{"type":["string","null"]},"reason":{"type":["string","null"]},
            "date":{"type":["string","null"]},"time":{"type":["string","null"]},"shift":{"type":["string","null"]},
            "guide_condition":{"type":["string","null"]},"old_ready":{"type":["integer","null"]},"new_ready":{"type":["integer","null"]},
            "confidence":{"type":"number"}
        },"required":["type","confidence"]}},
        "warnings":{"type":"array","items":{"type":"string"}}
    },"required":["actions","warnings"]
}

PROMPT = '''You are the Digital Stand Register report interpreter for a wire rod mill.
Extract operations only; never invent missing facts.
Vocabulary: WRM#1=W1, WRM#2=W2, WRM#3=W3. HT=HYDROTEST. Gauge/gauging=GAUGING.
Stand workflow: YET_TO_READY -> PENDING -> GAUGING -> HYDROTEST -> READY -> RUNNING.
Only stands at positions 2,4,6,8,10 use entry guides.
For a stand change extract old/new stand, line, position, people, reason, date/time/shift when present.
For readiness reports create STAND_STATUS actions. If text says a test is pending, do NOT claim it is completed; add a warning if exact current stage is unclear.
For entry guide stock summaries create ENTRY_GUIDE_SUMMARY with position and old_ready/new_ready counts.
For entry guide changes create ENTRY_GUIDE_CHANGE and preserve New/Old condition.
Use confidence 0..1. Ambiguous facts belong in warnings, not guesses.
REPORT:\n'''

def _value(text, label):
    m=re.search(rf"(?im)^\s*{label}\s*[:-]\s*(.+?)\s*$",text); return m.group(1).strip() if m else None

def _stand_list(text, heading):
    m=re.search(rf"(?is){heading}\s*:?(.*?)(?=\n\s*(?:READY|HYDROTEST|GAUGING|PENDING|YET TO READY|ENTRY GUIDES?|STAND CHANGE)\s*:|$)",text)
    return re.findall(r"\b(?:10|[1-9])(?:\.[1-9]|[A-E])\b",m.group(1),flags=re.I) if m else []

def template_parse(text):
    actions=[]; warnings=[]; removed=_value(text,r"Stand\s*Remove"); fixed=_value(text,r"Stand\s*Fixed"); line=_value(text,r"Line")
    if not line:
        wrm=re.search(r"(?i)WRM\s*#?\s*([123])",text); line=f"W{wrm.group(1)}" if wrm else None
    if removed and fixed:
        pos=re.match(r"(10|[1-9])",fixed); actions.append({"type":"STAND_CHANGE","line":line,"position":int(pos.group(1)) if pos else None,"stand_removed":removed,"stand_fixed":fixed,"done_by":_value(text,r"(?:Changed By|S\.I\.)"),"reason":_value(text,r"Reason"),"date":_value(text,r"Date"),"time":_value(text,r"Time"),"shift":_value(text,r"Shift"),"confidence":0.95})
    for heading,status in [("READY","READY"),("HYDROTEST","HYDROTEST"),("GAUGING","GAUGING"),("PENDING","PENDING"),("YET TO READY","YET_TO_READY")]:
        for code in _stand_list(text,heading): actions.append({"type":"STAND_STATUS","stand":code.upper(),"status":status,"confidence":0.95})
    if not actions: warnings.append("No supported operation confidently detected by fallback parser.")
    return {"actions":actions,"warnings":warnings}

def gemini_parse(text):
    key=os.getenv("GEMINI_API_KEY")
    if not key: raise RuntimeError("GEMINI_API_KEY not configured")
    model=os.getenv("GEMINI_MODEL","gemini-2.5-flash-lite")
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body={"contents":[{"parts":[{"text":PROMPT+text}]}],"generationConfig":{"temperature":0.1,"responseMimeType":"application/json","responseJsonSchema":SCHEMA}}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":key},method="POST")
    with urllib.request.urlopen(req,timeout=20) as response: raw=json.loads(response.read().decode())
    result_text=raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(result_text)

@router.post("/analyse")
def analyse_report(payload: ReportInput, user: User = Depends(require_operator)):
    text=payload.text.strip(); provider="gemini"
    try:
        parsed=gemini_parse(text)
    except Exception as exc:
        provider="template-parser"; parsed=template_parse(text); parsed["warnings"].append("AI unavailable; used free template parser instead.")
    return {"provider":provider,"analysed_by":user.username,"actions":parsed.get("actions",[]),"warnings":parsed.get("warnings",[]),"message":"Preview only. No plant data has been changed."}
