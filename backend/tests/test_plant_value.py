from datetime import datetime,timedelta,date
from uuid import uuid4
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
import app.models
from app.database.session import Base,get_db
from app.models.user import User
from app.models.line import Line
from app.models.line_runtime import LineRuntimeEvent
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.inventory_item import InventoryItem
from app.models.plant_measurement import PreparationCycle,MaintenanceMeasurement,RuntimeConfirmation
from app.models.enums import StatusEnum
from app.models.command_receipt import CommandReceipt
from app.services.operation_service import OperationService
from app.services.plant_value_service import PlantValueService
from app.api.routes.plant import start_preparation,confirm,Confirmation,measure,MeasurementInput,baseline,BaselineInput
from app.main import app
from app.auth.jwt import create_access_token
from test_feedback import asgi

@pytest.fixture
def db():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            predicate=index.dialect_options['postgresql'].get('where')
            if predicate is not None:index.dialect_options['sqlite']['where']=predicate
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([User(id=1,username='value-admin',role_id=1,hashed_password='test-only'),User(id=2,username='value-operator',role_id=2,hashed_password='test-only')]);db.commit();yield db
    engine.dispose()

def test_explicit_preparation_start_is_idempotent_and_ready_closes_measured_cycle(db):
    stand=StandAsset(code='1A',current_status=StatusEnum.HYDROTEST);db.add(stand);db.commit()
    user=db.get(User,2)
    first=start_preparation(stand.id,db,user)
    assert start_preparation(stand.id,db,user)['id']==first['id']
    cycle=db.get(PreparationCycle,first['id']);cycle.started_at=datetime.utcnow()-timedelta(hours=4);db.commit()
    OperationService(db).update_preparation_status('1A',StatusEnum.READY,user.id,user.username)
    assert cycle.finished_at is not None and cycle.finished_by==user.username
    evidence=PlantValueService(db).summary()['observed']['preparation_hours']
    assert evidence['samples']==1 and evidence['average']==4
    with pytest.raises(HTTPException):start_preparation(stand.id,db,user)

def test_failed_transaction_does_not_close_preparation_measurement(db):
    stand=StandAsset(code='1A',current_status=StatusEnum.HYDROTEST);db.add(stand);db.commit()
    row=start_preparation(stand.id,db,db.get(User,2));cycle_id=row['id']
    OperationService(db,auto_commit=False).update_preparation_status('1A',StatusEnum.READY,2,'Operator')
    db.rollback()
    assert db.get(PreparationCycle,cycle_id).finished_at is None
    assert db.get(StandAsset,stand.id).current_status==StatusEnum.HYDROTEST

def test_confirmation_never_invents_history_or_changes_runtime_state(db):
    now=datetime.utcnow();line=Line(name='W4');db.add(line);db.flush()
    pos=Position(line_id=line.id,position_number=1);db.add(pos);db.flush()
    stand=StandAsset(code='1A',current_status=StatusEnum.INSTALLED,current_position_id=pos.id);db.add(stand);db.flush()
    db.add(StandInstallation(stand_id=stand.id,position_id=pos.id,installed_at=now-timedelta(days=2)));db.commit()
    with pytest.raises(HTTPException):confirm(line.id,Confirmation(state='RUNNING'),db,db.get(User,2))
    db.add(LineRuntimeEvent(line_id=line.id,state='RUNNING',event_at=now-timedelta(hours=12),recorded_by='Operator'));db.commit()
    confirm(line.id,Confirmation(state='RUNNING'),db,db.get(User,2))
    assert db.query(LineRuntimeEvent).count()==1 and db.query(RuntimeConfirmation).count()==1
    data=PlantValueService(db).summary()
    assert data['runtime']['complete_campaigns']==0 and not data['lines'][0]['needs_confirmation']
    with pytest.raises(HTTPException):confirm(line.id,Confirmation(state='STOPPED'),db,db.get(User,2))

def test_measurements_and_baselines_are_separate_and_retries_do_not_duplicate(db):
    p=MeasurementInput(request_id=uuid4(),kind='INVESTIGATION',duration_minutes=40,description='Measured bearing investigation effort')
    first=measure(p,db,db.get(User,2));assert measure(p,db,db.get(User,2))==first
    assert db.query(MaintenanceMeasurement).count()==1 and db.query(CommandReceipt).count()==1
    data=PlantValueService(db).summary();assert data['estimates']==[] and data['observed']['investigation_minutes']['average']==40
    baseline('INVESTIGATION_MINUTES',BaselineInput(value=30,sample_count=5,period_start=date(2026,1,1),period_end=date(2026,1,31),source='January measured work study'),db,db.get(User,1))
    estimate=PlantValueService(db).summary()['estimates'][0]
    assert estimate['estimated_reduction_per_case']==-10 and estimate['current_samples']==1
    assert 'estimate' in estimate['basis']

@pytest.mark.parametrize('duration',[0,-1,float('nan'),float('inf')])
def test_invalid_effort_values_are_rejected(duration):
    with pytest.raises(ValidationError):MeasurementInput(request_id=uuid4(),kind='INVESTIGATION',duration_minutes=duration,description='Actual recorded effort')

def test_stock_snapshot_is_not_reported_shortage_and_unknown_is_not_zero(db):
    db.add_all([InventoryItem(name='Unknown',quantity=None),InventoryItem(name='Below minimum',quantity=2,minimum_quantity=5),InventoryItem(name='Empty',quantity=0)]);db.commit()
    data=PlantValueService(db).summary()
    assert data['stock']['unknown_balances']==1 and len(data['stock']['at_risk'])==2
    assert data['observed']['reported_shortages']==0
    assert data['observed']['preparation_hours']['average'] is None
    assert data['observed']['record_completeness']['percent'] is None

def test_staging_blocks_mutations_and_baselines_require_admin(db,monkeypatch):
    app.dependency_overrides[get_db]=lambda:db
    try:
        assert asgi('PUT','/api/v1/plant/baselines/PREPARATION_HOURS',{})==401
        token=create_access_token({'sub':'value-operator'})
        assert asgi('PUT','/api/v1/plant/baselines/PREPARATION_HOURS',{},token)==403
        monkeypatch.setenv('DSR_ENVIRONMENT','staging')
        assert asgi('POST','/api/v1/runtime/lines',{'name':'unsafe'},token)==403
        assert asgi('GET','/api/v1/plant/environment')==200
    finally:app.dependency_overrides.clear()

def test_staging_fixture_refuses_production_and_is_repeatable(db):
    from scripts.staging_fixture import validate_target,seed
    with pytest.raises(RuntimeError):validate_target('postgresql://localhost/digital_stand_register','staging')
    with pytest.raises(RuntimeError):validate_target('postgresql://localhost/dsr_staging','production')
    validate_target('postgresql://localhost/dsr_staging','staging')
    seed(db);seed(db)
    assert db.query(Line).count()==2 and all(row.name.startswith('DEMO-') for row in db.query(Line).all())
