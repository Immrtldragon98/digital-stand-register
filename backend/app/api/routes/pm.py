from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import require_operator, require_admin
from app.database.session import get_db
from app.models.pm_activity import PMActivity
from app.models.user import User
router=APIRouter()
STATUSES={"PLANNED","DUE","COMPLETED","DEFERRED"}

class PMInput(BaseModel):
    planned_date: date
    line_name: str|None=Field(default=None,max_length=16)
    equipment: str=Field(min_length=1,max_length=120)
    activity: str=Field(min_length=1,max_length=255)
    frequency: str|None=Field(default=None,max_length=40)
    assigned_to: str|None=Field(default=None,max_length=100)
    status: str="PLANNED"
    completed_date: date|None=None
    remarks: str|None=Field(default=None,max_length=2000)

def out(x):
    return {c:getattr(x,c) for c in ["id","planned_date","line_name","equipment","activity","frequency","assigned_to","status","completed_date","remarks","created_by","updated_by","created_at","updated_at"]}

def apply(x,p,user):
    status=p.status.strip().upper()
    if status not in STATUSES: raise HTTPException(400,"Invalid PM status")
    x.planned_date=p.planned_date
    x.line_name=(p.line_name or "").strip().upper() or None
    x.equipment=p.equipment.strip()
    x.activity=p.activity.strip()
    x.frequency=(p.frequency or "").strip() or None
    x.assigned_to=(p.assigned_to or "").strip() or None
    x.status=status
    x.completed_date=p.completed_date or (date.today() if status=="COMPLETED" else None)
    x.remarks=(p.remarks or "").strip() or None
    x.updated_by=user.username
    x.updated_at=datetime.utcnow()

@router.get("/")
def list_pm(start:date|None=None,end:date|None=None,line:str|None=None,status:str|None=None,db:Session=Depends(get_db)):
    q=db.query(PMActivity)
    if start:q=q.filter(PMActivity.planned_date>=start)
    if end:q=q.filter(PMActivity.planned_date<=end)
    if line:q=q.filter(PMActivity.line_name==line.upper())
    if status:q=q.filter(PMActivity.status==status.upper())
    return [out(x) for x in q.order_by(PMActivity.planned_date.asc(),PMActivity.id.asc()).all()]

@router.post("/")
def create_pm(p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    x=PMActivity(created_by=user.username,updated_by=user.username,created_at=datetime.utcnow(),updated_at=datetime.utcnow())
    apply(x,p,user);db.add(x);db.commit();db.refresh(x);return out(x)

@router.put("/{pm_id}")
def update_pm(pm_id:int,p:PMInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    x=db.get(PMActivity,pm_id)
    if not x:raise HTTPException(404,"PM activity not found")
    apply(x,p,user);db.commit();db.refresh(x);return out(x)

@router.delete("/{pm_id}")
def delete_pm(pm_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    x=db.get(PMActivity,pm_id)
    if not x:raise HTTPException(404,"PM activity not found")
    db.delete(x);db.commit();return {"status":"deleted"}
