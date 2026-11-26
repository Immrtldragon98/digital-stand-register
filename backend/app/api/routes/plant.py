import json, os
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin, require_operator
from app.database.session import get_db
from app.models.activity_log import ActivityLog
from app.models.inventory_item import InventoryItem
from app.models.line import Line
from app.models.line_runtime import LineRuntimeEvent
from app.models.plant_measurement import MaintenanceMeasurement, PreparationCycle, RuntimeConfirmation, ValueBaseline
from app.models.stand_asset import StandAsset
from app.models.user import User
from app.services.command_service import run_command
from app.services.plant_value_service import PlantValueService

router=APIRouter()


@router.get('/environment')
def environment():
    staging=os.getenv('DSR_ENVIRONMENT','production')=='staging'
    return {'name':'staging' if staging else 'production','read_only':staging,'hosting':'free-sleeping',
        'availability_note':'Free API hosting can sleep after inactivity. Saved views are labelled; current operations require a connection.'}


@router.get('/summary')
def summary(days:int=Query(30,ge=1,le=365),db:Session=Depends(get_db)):
    return PlantValueService(db).summary(days)


@router.get('/dependability')
def dependability(db:Session=Depends(get_db),user:User=Depends(require_admin)):
    proof=Path(__file__).parents[3]/'ops'/'recovery.json'
    evidence=json.loads(proof.read_text()) if proof.exists() else {'status':'NOT_VERIFIED'}
    return {'environment':environment(),'recovery':evidence,'snapshot_schedule':'NOT_AVAILABLE_ON_CURRENT_ACCOUNT',
        'runtime':PlantValueService(db).summary()['runtime'],'next_steps':['Record initial line states and confirm them each shift.','Review missing attribution and removal reasons.','Take a fresh snapshot before each production migration.','Repeat the isolated restore check after schema changes.']}


@router.get('/preparations/{stand_id}')
def preparation(stand_id:int,db:Session=Depends(get_db)):
    row=db.query(PreparationCycle).filter_by(stand_id=stand_id).order_by(PreparationCycle.started_at.desc()).first()
    return {'id':row.id,'started_at':row.started_at,'started_by':row.started_by,'finished_at':row.finished_at} if row else None


@router.post('/preparations/{stand_id}/start')
def start_preparation(stand_id:int,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    stand=db.query(StandAsset).filter_by(id=stand_id).with_for_update().first()
    if not stand:raise HTTPException(404,'Stand not found.')
    if stand.current_position_id is not None or stand.current_status in {'INSTALLED','READY'}:raise HTTPException(409,'Start preparation only for a stand in the preparation workflow.')
    row=db.query(PreparationCycle).filter_by(stand_id=stand_id,finished_at=None).first()
    if not row:
        row=PreparationCycle(stand_id=stand_id,started_by=user.username,started_at=datetime.utcnow());db.add(row)
        db.add(ActivityLog(user_id=user.id,action='START_PREPARATION_TIMER',details=f'Started explicit preparation measurement for stand {stand.code}.',timestamp=datetime.utcnow()))
        db.commit();db.refresh(row)
    return {'id':row.id,'started_at':row.started_at,'started_by':row.started_by,'finished_at':row.finished_at}


class Confirmation(BaseModel):
    state:Literal['RUNNING','STOPPED']


@router.post('/runtime/{line_id}/confirm')
def confirm(line_id:int,payload:Confirmation,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    line=db.query(Line).filter_by(id=line_id).with_for_update().first()
    if not line:raise HTTPException(404,'Line not found.')
    latest=db.query(LineRuntimeEvent).filter_by(line_id=line_id).order_by(LineRuntimeEvent.event_at.desc()).first()
    if latest is None:raise HTTPException(409,'Record the initial running or stopped state first.')
    if latest.state!=payload.state:raise HTTPException(409,'Line state changed. Refresh before confirming.')
    row=RuntimeConfirmation(line_id=line_id,state=payload.state,confirmed_by=user.username,confirmed_at=datetime.utcnow())
    db.add(row);db.commit()
    return {'line_id':line_id,'state':row.state,'confirmed_at':row.confirmed_at,'message':'Current state confirmed. Historical runtime was not changed.'}


class MeasurementInput(BaseModel):
    request_id:UUID
    kind:Literal['INVESTIGATION','SPARE_SHORTAGE']
    duration_minutes:float|None=Field(default=None,gt=0,le=10080,allow_inf_nan=False)
    description:str=Field(min_length=5,max_length=2000)
    stand_id:int|None=None
    item_id:int|None=None
    @field_validator('description',mode='before')
    @classmethod
    def trim(cls,value):return value.strip() if isinstance(value,str) else value


@router.post('/measurements',status_code=201)
def measure(payload:MeasurementInput,db:Session=Depends(get_db),user:User=Depends(require_operator)):
    if payload.kind=='INVESTIGATION' and payload.duration_minutes is None:raise HTTPException(400,'Record the actual investigation minutes.')
    for model,identifier in [(StandAsset,payload.stand_id),(InventoryItem,payload.item_id)]:
        if identifier is not None and db.get(model,identifier) is None:raise HTTPException(404,'Linked stand or spare was not found.')
    def save():
        row=MaintenanceMeasurement(**payload.model_dump(exclude={'request_id'}),request_id=str(payload.request_id),recorded_by=user.username,recorded_at=datetime.utcnow())
        db.add(row);db.flush();return {'id':row.id,'kind':row.kind,'recorded_at':row.recorded_at.isoformat()}
    return run_command(db,user.id,str(payload.request_id),'MAINTENANCE_MEASUREMENT',payload.model_dump(mode='json'),save)


class BaselineInput(BaseModel):
    value:float=Field(gt=0,allow_inf_nan=False)
    sample_count:int=Field(ge=1)
    period_start:date
    period_end:date
    source:str=Field(min_length=5,max_length=500)


@router.put('/baselines/{metric}')
def baseline(metric:Literal['PREPARATION_HOURS','INVESTIGATION_MINUTES'],payload:BaselineInput,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    if payload.period_end<payload.period_start or payload.period_end>datetime.now(ZoneInfo('Asia/Kolkata')).date():raise HTTPException(400,'Use a completed baseline period with a valid start and end.')
    if not payload.source.strip():raise HTTPException(400,'Baseline source is required.')
    row=db.get(ValueBaseline,metric)
    before=row.value if row else None
    if row is None:row=ValueBaseline(metric=metric);db.add(row)
    for key,value in payload.model_dump().items():setattr(row,key,value)
    row.recorded_by=user.username;row.updated_at=datetime.utcnow()
    db.add(ActivityLog(user_id=user.id,action='UPDATE_VALUE_BASELINE',details=f'{metric}: {before} -> {payload.value}; n={payload.sample_count}; source={payload.source}',timestamp=datetime.utcnow()))
    db.commit();return {'metric':metric,'value':row.value}
