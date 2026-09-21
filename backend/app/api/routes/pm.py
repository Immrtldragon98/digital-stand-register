import json, os, urllib.request, urllib.parse
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import require_operator, require_admin
from app.database.session import get_db
from app.models.pm_activity import PMActivity
from app.models.user import User\nfrom app.models.line import Line\nfrom app.models.stand_position import Position\nfrom app.schemas.operation import ChangeStandSchema\nfrom app.services.operation_service import OperationService
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
class MessageInput(BaseModel): text:str
class ConfirmInput(BaseModel): activities:list[dict]; source_text:str|None=None

FIELDS=["id","planned_date","line_name","shift","position_number","stand_code","equipment","component","activity_type","activity","from_value","to_value","assigned_to","status","completed_date","remarks","source_text","created_by","updated_by","created_at","updated_at"]
def out(x): return {c:getattr(x,c) for c in FIELDS}
def apply(x,p,user):
    s=p.status.strip().upper()
    if s not in STATUSES: raise HTTPException(400,"Invalid status")
    x.planned_date=p.planned_date;x.line_name=(p.line_name or "").strip().upper() or None;x.shift=(p.shift or "").strip().upper() or None;x.position_number=p.position_number;x.stand_code=(p.stand_code or "").strip().upper() or None;x.equipment=p.equipment.strip();x.component=(p.component or "").strip() or None;x.activity_type=(p.activity_type or "OTHER").strip().upper();x.activity=p.activity.strip();x.from_value=(p.from_value or "").strip() or None;x.to_value=(p.to_value or "").strip() or None;x.assigned_to=(p.assigned_to or "").strip() or None;x.status=s;x.completed_date=p.completed_date or (p.planned_date if s=="COMPLETED" else None);x.remarks=(p.remarks or "").strip() or None;x.source_text=p.source_text;x.updated_by=user.username;x.updated_at=datetime.utcnow()

@router.get("/")
def list_pm(start:date|None=None,end:date|None=None,line:str|None=None,status:str|None=None,db:Session=Depends(get_db)):
    q=db.query(PMActivity)
    if start:q=q.filter(PMActivity.planned_date>=start)
    if end:q=q.filter(PMActivity.planned_date<=end)
    if line:q=q.filter(PMActivity.line_name==line.upper())
    if status:q=q.filter(PMActivity.status==status.upper())
    return [out(x) for x in q.order_by(PMActivity.planned_date.desc(),PMActivity.id.desc()).all()]
@router.post("/")
def create_pm(p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    x=PMActivity(created_by=user.username,updated_by=user.username,created_at=datetime.utcnow(),updated_at=datetime.utcnow());apply(x,p,user);db.add(x);db.commit();db.refresh(x);return out(x)
@router.put("/{pm_id}")
def update_pm(pm_id:int,p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
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
    today=date.today().isoformat(); dm=re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",text)
    if dm:
        y=int(dm.group(3));y=y+2000 if y<100 else y; day=f"{y:04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
    else: day=today
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
        with urllib.request.urlopen(req,timeout=20) as r: raw=json.loads(r.read().decode())
        parsed=json.loads(raw["candidates"][0]["content"]["parts"][0]["text"]);return parsed.get("activities",[]),model
    except Exception:return fallback(text),"template-parser"

@router.post("/analyse-message")
def analyse_message(p:MessageInput,user:User=Depends(require_operator)):
    acts,provider=ai_parse(p.text.strip())
    rows=[]
    for i,a in enumerate(acts):
        missing=[] 
        if not a.get("planned_date"):missing.append("date")
        if not a.get("equipment"):missing.append("equipment")
        state="READY" if float(a.get("confidence") or 0)>=.75 and not missing else "REVIEW"
        rows.append({"index":i,"state":state,"missing":missing,"activity":a})
    return {"provider":provider,"activities":rows,"message":"Preview only. Review before saving."}

@router.post("/confirm-message")
def confirm_message(p:ConfirmInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    saved=[]
    for a in p.activities:
        try: payload=PMInput(**{**a,"source_text":p.source_text,"status":a.get("status","COMPLETED")})
        except Exception as e: saved.append({"status":"SKIPPED","message":str(e),"activity":a});continue
        x=PMActivity(created_by=user.username,updated_by=user.username,created_at=datetime.utcnow(),updated_at=datetime.utcnow());apply(x,payload,user);db.add(x);saved.append({"status":"SAVED","activity":a})
    db.commit()
    # Only execute an existing DSR operation when the reviewed row has every mandatory fact.
    # The LLM never bypasses OperationService validation.
    performed=[]
    service=OperationService(db)
    for a in p.activities:
        if (a.get("activity_type") or "").upper()!="STAND_CHANGE": continue
        required=[a.get("line_name"),a.get("position_number"),a.get("from_value"),a.get("to_value"),a.get("assigned_to"),a.get("remarks")]
        if not all(required):
            performed.append({"status":"REVIEW_ONLY","activity":a,"message":"Stored in maintenance history. Stand change not executed because line, position, old/new stand, changed-by or reason is missing."});continue
        line=db.query(Line).filter(Line.name==str(a["line_name"]).upper()).first()
        pos=db.query(Position).filter(Position.line_id==line.id,Position.position_number==int(a["position_number"])).first() if line else None
        if not pos:
            performed.append({"status":"NOT_PERFORMED","activity":a,"message":"Line/position not found."});continue
        try:
            when=datetime.combine(date.fromisoformat(a["planned_date"]),datetime.min.time())
            result=service.change_stand(ChangeStandSchema(position_id=pos.id,removed_stand_code=str(a["from_value"]).upper(),installed_stand_code=str(a["to_value"]).upper(),changed_by=str(a["assigned_to"]),reason=str(a["remarks"]),changed_at=when,notes="Confirmed from PM Activities message import"),user.id)
            performed.append({"status":"PERFORMED","activity":a,"result":result})
        except Exception as exc:
            db.rollback();performed.append({"status":"NOT_PERFORMED","activity":a,"message":getattr(exc,"detail",str(exc))})
    return {"saved":sum(1 for x in saved if x["status"]=="SAVED"),"results":saved,"operations":performed,"confirmed_by":user.username}
