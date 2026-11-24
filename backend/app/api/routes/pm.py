import json, os, urllib.request, urllib.parse
from datetime import date, datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Annotated
from pydantic import ValidationError
from app.auth.dependencies import ADMIN_ROLE_ID
from app.services.command_service import run_command
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import require_operator, require_admin
from app.database.session import get_db
from app.models.pm_activity import PMActivity
from app.models.user import User
from app.models.line import Line
from app.models.stand_position import Position
from app.schemas.operation import ChangeStandSchema
from app.services.operation_service import OperationService
router=APIRouter()
STATUSES={"PLANNED","DUE","COMPLETED","DEFERRED"}
TYPES={"STAND_CHANGE","COUPLER_CHANGE","PIVOT_CHANGE","ENTRY_GUIDE","BEARING","OIL_SEAL","LUBRICATION","INSPECTION","ADJUSTMENT","BREAKDOWN","OTHER"}

class PMInput(BaseModel):
    planned_date: date
    line_name: str|None=None
    shift: str|None=None
    position_number: int|None=None
    stand_code: str|None=None
    equipment: str=Field(min_length=1,max_length=120)
    component: str|None=None
    activity_type: str="OTHER"
    activity: str=Field(min_length=1,max_length=255)
    from_value: str|None=None
    to_value: str|None=None
    assigned_to: str|None=None
    status: str="COMPLETED"
    completed_date: date|None=None
    remarks: str|None=None
    source_text: str|None=None
class MessageInput(BaseModel): text:str=Field(min_length=1,max_length=20000)
class ConfirmInput(BaseModel): activities:list[dict]=Field(min_length=1,max_length=100); source_text:str|None=Field(default=None,max_length=20000)

FIELDS=["id","planned_date","line_name","shift","position_number","stand_code","equipment","component","activity_type","activity","from_value","to_value","assigned_to","status","completed_date","remarks","source_text","created_by","updated_by","created_at","updated_at"]
def out(x): return {c:getattr(x,c) for c in FIELDS}
def apply(x,p,user):
    s=p.status.strip().upper()
    if s not in STATUSES: raise HTTPException(400,"Invalid status")
    if p.activity_type.strip().upper() not in TYPES: raise HTTPException(400,"Invalid activity type")
    if not p.equipment.strip() or not p.activity.strip(): raise HTTPException(400,"Equipment and activity are required")
    x.planned_date=p.planned_date;x.line_name=(p.line_name or "").strip().upper() or None;x.shift=(p.shift or "").strip().upper() or None;x.position_number=p.position_number;x.stand_code=(p.stand_code or "").strip().upper() or None;x.equipment=p.equipment.strip();x.component=(p.component or "").strip() or None;x.activity_type=(p.activity_type or "OTHER").strip().upper();x.activity=p.activity.strip();x.from_value=(p.from_value or "").strip() or None;x.to_value=(p.to_value or "").strip() or None;x.assigned_to=(p.assigned_to or "").strip() or None;x.status=s;x.completed_date=p.completed_date or (p.planned_date if s=="COMPLETED" else None);x.remarks=(p.remarks or "").strip() or None;x.source_text=p.source_text;x.updated_by=user.username;x.updated_at=datetime.utcnow()

@router.get("/")
def list_pm(start:date|None=None,end:date|None=None,line:str|None=None,status:str|None=None,db:Session=Depends(get_db)):
    q=db.query(PMActivity)
    if start:q=q.filter(PMActivity.planned_date>=start)
    if end:q=q.filter(PMActivity.planned_date<=end)
    if line:q=q.filter(PMActivity.line_name==line.upper())
    if status:q=q.filter(PMActivity.status==status.upper())
    return [out(x) for x in q.order_by(PMActivity.planned_date.desc(),PMActivity.id.desc()).limit(2000).all()]
@router.post("/")
def create_pm(p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    _check_backdate(p,user)
    x=PMActivity(created_by=user.username,updated_by=user.username,created_at=datetime.utcnow(),updated_at=datetime.utcnow());apply(x,p,user);db.add(x);db.commit();db.refresh(x);return out(x)
@router.put("/{pm_id}")
def update_pm(pm_id:int,p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    x=db.get(PMActivity,pm_id)
    if not x:raise HTTPException(404,"Activity not found")
    apply(x,p,user);db.commit();db.refresh(x);return out(x)
@router.delete("/{pm_id}")
def delete_pm(pm_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    x=db.get(PMActivity,pm_id)
    if not x:raise HTTPException(404,"Activity not found")
    db.delete(x);db.commit();return {"status":"deleted"}

PROMPT="""Extract completed industrial maintenance activities from the message. Never invent missing facts.
Return JSON object with activities array. Each activity: planned_date YYYY-MM-DD, line_name W1/W2/W3/null, shift A/B/C/G/null, position_number integer/null, stand_code/null, equipment, component/null, activity_type one of STAND_CHANGE COUPLER_CHANGE PIVOT_CHANGE ENTRY_GUIDE BEARING OIL_SEAL LUBRICATION INSPECTION ADJUSTMENT BREAKDOWN OTHER, activity, from_value/null, to_value/null, assigned_to/null, remarks/null, confidence 0..1.
One physical maintenance action = one row. Preserve stand IDs and component names. If a field is absent use null. Do not infer people or dates. MESSAGE:\n"""

def fallback(text):
    import re
    dm=re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",text)
    if dm:
        y=int(dm.group(3));y=y+2000 if y<100 else y; day=f"{y:04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
    else: day=None
    lm=re.search(r"\bW(?:RM)?\s*#?\s*([123])\b",text,re.I);line="W"+lm.group(1) if lm else None
    sm=re.search(r"\b([ABCG])\s*shift\b",text,re.I);shift=sm.group(1).upper() if sm else None
    acts=[]
    patterns=[("STAND_CHANGE","Stand","Stand",r"(?i)stand\s*(?:(10|[1-9])\s*)?(?:changed|change)\s*(?:from\s*)?([\w.]+)\s*(?:to|->)\s*([\w.]+)"),("COUPLER_CHANGE","Coupler","Coupler",r"(?i)(?:P(?:osition)?\s*)?(10|[1-9])\s*coupler\s*(?:changed|replaced)"),("PIVOT_CHANGE","Pivot","Pivot",r"(?i)(?:P(?:osition)?\s*)?(10|[1-9])\s*pivot\s*(?:changed|replaced)"),("ENTRY_GUIDE","Entry Guide","Entry Guide",r"(?i)entry\s*guide\s*(?:at\s*)?(?:P)?(10|[2468]).*?(?:changed|replaced)")]
    for typ,equip,comp,pat in patterns:
        for m in re.finditer(pat,text):
            pos=int(m.group(1)) if m.group(1) else None; frm=m.group(2).upper() if typ=="STAND_CHANGE" else None;to=m.group(3).upper() if typ=="STAND_CHANGE" else None
            acts.append({"planned_date":day,"line_name":line,"shift":shift,"position_number":pos,"stand_code":to if typ=="STAND_CHANGE" else None,"equipment":equip,"component":comp,"activity_type":typ,"activity":typ.replace("_"," ").title(),"from_value":frm,"to_value":to,"assigned_to":None,"remarks":None,"confidence":.8})
    return acts

def ai_parse(text):
    key=os.getenv("GEMINI_API_KEY")
    if not key:return fallback(text),"template-parser"
    model=(os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    body={"contents":[{"parts":[{"text":PROMPT+text}]}],"generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}}
    req=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model,safe='')}:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":key},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: raw=json.loads(r.read(2_000_001).decode())
        parsed=json.loads(raw["candidates"][0]["content"]["parts"][0]["text"]);return parsed.get("activities",[]),model
    except Exception:return fallback(text),"template-parser"

@router.post("/analyse-message")
def analyse_message(p:MessageInput,user:User=Depends(require_operator)):
    acts,provider=ai_parse(p.text.strip())
    rows=[]
    if not isinstance(acts,list): raise HTTPException(502,"AI returned an invalid activity list")
    for i,a in enumerate(acts[:100]):
        if not isinstance(a,dict): continue
        missing=[] 
        if not a.get("planned_date"):missing.append("date")
        if not a.get("equipment"):missing.append("equipment")
        try: confidence=float(a.get("confidence") or 0)
        except (ValueError,TypeError): confidence=0
        state="READY" if 0.75<=confidence<=1 and not missing else "REVIEW"
        rows.append({"index":i,"state":state,"missing":missing,"activity":a})
    return {"provider":provider,"activities":rows,"message":"Preview only. Review before saving."}

def _check_backdate(payload, user):
    today=datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if user.role_id != ADMIN_ROLE_ID and (payload.planned_date < today or (payload.completed_date and payload.completed_date < today)):
        raise HTTPException(403, "Only an admin can enter backdated maintenance records.")


@router.post("/confirm-message")
def confirm_message(p:ConfirmInput,db:Session=Depends(get_db),user:User=Depends(require_operator), idempotency_key: Annotated[str|None, Header()] = None):
    def save():
        rows=[]
        for item in p.activities:
            try:
                payload=PMInput(**{**item,"source_text":p.source_text,"status":item.get("status","COMPLETED")})
            except ValidationError:
                raise HTTPException(400,"Every selected activity needs a valid date, equipment and activity. No rows were saved.")
            _check_backdate(payload,user)
            row=PMActivity(created_by=user.username,updated_by=user.username,created_at=datetime.utcnow(),updated_at=datetime.utcnow())
            apply(row,payload,user)
            rows.append(row)
        db.add_all(rows)
        db.flush()
        return {"saved":len(rows),"results":[{"status":"SAVED","id":row.id} for row in rows],"operations":[],"confirmed_by":user.username,"message":"Maintenance history saved only. No stand or stock operation was executed."}
    return run_command(db,user.id,idempotency_key,'PM_IMPORT',p.model_dump(),save)
