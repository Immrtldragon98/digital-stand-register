from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.auth.dependencies import require_admin, require_operator, ADMIN_ROLE_ID
from app.models.line import Line
from app.models.line_runtime import LineRuntimeEvent
from app.models.stand_position import Position
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.services.runtime_service import RuntimeService, utc_naive

router=APIRouter()
class StateInput(BaseModel):
    state:str=Field(pattern='^(RUNNING|STOPPED)$')
    event_at:datetime|None=None
    reason:str|None=Field(default=None,max_length=500)
class Correction(StateInput):
    correction_reason:str=Field(min_length=3,max_length=500)
class LineInput(BaseModel):
    name:str=Field(min_length=1,max_length=50)

@router.get('/lines')
def lines(db:Session=Depends(get_db)):
    service=RuntimeService(db)
    return [{'id':line.id,'name':line.name,'state':service.events[line.id][-1].state if service.events[line.id] else 'UNKNOWN',
             'tracking_started_at':service.events[line.id][0].event_at if service.events[line.id] else None,
             'last_event_at':service.events[line.id][-1].event_at if service.events[line.id] else None,
             'planned_pm_hours_per_month':12,'event_count':len(service.events[line.id]),'history_truncated':len(service.events[line.id])>100,'events':[{'id':e.id,'state':e.state,'event_at':e.event_at,'reason':e.reason,'recorded_by':e.recorded_by} for e in service.events[line.id][-100:]]}
            for line in db.query(Line).order_by(Line.id).all()]

@router.post('/lines',status_code=201)
def create_line(payload:LineInput,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    name=payload.name.strip().upper()
    if not name: raise HTTPException(400,'Line name is required.')
    line=Line(name=name);db.add(line)
    try:
        db.flush()
        db.add_all([Position(line_id=line.id,position_number=i) for i in range(1,11)])
        db.add(ActivityLog(user_id=user.id,action='CREATE_LINE',timestamp=datetime.utcnow(),details=f'Created {name} with 10 positions.'))
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Line already exists.')
    return {'id':line.id,'name':line.name}

@router.post('/lines/{line_id}/state',status_code=201)
def set_state(line_id:int,payload:StateInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    line=db.query(Line).filter_by(id=line_id).with_for_update().first()
    if not line:raise HTTPException(404,'Line not found.')
    if payload.event_at is not None and user.role_id!=ADMIN_ROLE_ID:raise HTTPException(403,'Only admins may enter historical runtime.')
    at=utc_naive(payload.event_at) if payload.event_at else datetime.utcnow()
    if at>datetime.utcnow():raise HTTPException(400,'Runtime cannot be in the future.')
    last=db.query(LineRuntimeEvent).filter_by(line_id=line_id).order_by(LineRuntimeEvent.event_at.desc()).first()
    if last and at<=last.event_at:raise HTTPException(409,'New runtime event must follow the latest event; use admin correction for existing history.')
    if last and last.state==payload.state:raise HTTPException(409,'Line is already in this state.')
    row=LineRuntimeEvent(line_id=line_id,state=payload.state,event_at=at,recorded_by=user.username,reason=payload.reason)
    db.add(row);db.commit()
    return {'id':row.id,'line_id':line_id,'state':row.state,'event_at':row.event_at}

@router.patch('/events/{event_id}')
def correct_event(event_id:int,payload:Correction,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    if not payload.correction_reason.strip():raise HTTPException(400,'Correction reason is required.')
    row=db.get(LineRuntimeEvent,event_id)
    if not row:raise HTTPException(404,'Runtime event not found.')
    db.query(Line).filter_by(id=row.line_id).with_for_update().one()
    db.refresh(row)
    at=utc_naive(payload.event_at) if payload.event_at else row.event_at
    if at>datetime.utcnow():raise HTTPException(400,'Runtime cannot be in the future.')
    before=db.query(LineRuntimeEvent).filter(LineRuntimeEvent.line_id==row.line_id,LineRuntimeEvent.id!=row.id,LineRuntimeEvent.event_at<row.event_at).order_by(LineRuntimeEvent.event_at.desc()).first()
    after=db.query(LineRuntimeEvent).filter(LineRuntimeEvent.line_id==row.line_id,LineRuntimeEvent.id!=row.id,LineRuntimeEvent.event_at>row.event_at).order_by(LineRuntimeEvent.event_at).first()
    if (before and at<=before.event_at) or (after and at>=after.event_at):raise HTTPException(409,'Correction cannot reorder runtime events.')
    old=f'{row.state} at {row.event_at.isoformat()}'
    row.event_at=at;row.state=payload.state;row.reason=payload.reason
    db.add(ActivityLog(user_id=user.id,action='CORRECT_LINE_RUNTIME',timestamp=datetime.utcnow(),details=f'Event {row.id}: {old} -> {row.state} at {at.isoformat()}. Reason: {payload.correction_reason.strip()}'))
    db.commit()
    return {'id':row.id,'state':row.state,'event_at':row.event_at}
