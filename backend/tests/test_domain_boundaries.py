from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.database.session import Base
from app.models.enums import LocationEnum, StatusEnum
from app.models.line import Line
from app.models.line_runtime import LineRuntimeEvent
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.stand_component import StandComponentType, StandComponentPreparation, StandComponentPreparationItem
from app.models.component_asset import ComponentAsset, ComponentFitting, PreparationAssetSelection
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.services.runtime_service import RuntimeService
from app.services.component_lifecycle_service import ComponentLifecycleService
from app.api.routes.runtime import Correction, correct_event

@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            predicate = index.dialect_options['postgresql'].get('where')
            if predicate is not None:
                index.dialect_options['sqlite']['where'] = predicate
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()

def preparation(db, quantity=2, condition='NEW', prior=0):
    start = datetime(2020,1,1)
    item = InventoryItem(name='Bearing',quantity=quantity)
    stand = StandAsset(code='1A',current_status=StatusEnum.PENDING,current_location=LocationEnum.WIP)
    db.add_all([item,stand]);db.flush()
    kind = StandComponentType(name='Bearing',required_qty=2,inventory_item_id=item.id)
    db.add(kind);db.flush()
    asset = ComponentAsset(code='BR-001',component_type_id=kind.id,condition=condition,prior_life_hours=prior,created_at=start)
    prep = StandComponentPreparation(stand_id=stand.id,state='SAVED',prepared_by='Operator',created_at=start)
    db.add_all([asset,prep]);db.flush()
    db.add(StandComponentPreparationItem(preparation_id=prep.id,component_type_id=kind.id,new_qty=int(condition=='NEW'),reused_qty=int(condition=='REUSED')))
    db.add(PreparationAssetSelection(preparation_id=prep.id,component_type_id=kind.id,asset_id=asset.id))
    db.commit()
    return item,stand,kind,asset,prep

def test_actual_runtime_does_not_certify_unverified_zero_lifetime(db):
    start=datetime(2020,1,1);end=start+timedelta(hours=10)
    line=Line(name='W1');db.add(line);db.flush()
    position=Position(line_id=line.id,position_number=1);db.add(position);db.flush()
    stand=StandAsset(code='1A',lifetime_hours=0);db.add(stand);db.flush()
    installation=StandInstallation(stand_id=stand.id,position_id=position.id,installed_at=start,removed_at=end)
    db.add_all([installation,LineRuntimeEvent(line_id=line.id,state='RUNNING',event_at=start,recorded_by='Operator'),
        LineRuntimeEvent(line_id=line.id,state='STOPPED',event_at=start+timedelta(hours=8),recorded_by='Operator')]);db.commit()
    runtime=RuntimeService(db)
    reading=runtime.measure(line.id,start,end)
    assert reading['hours']==8 and reading['elapsed_hours']==10
    assert runtime.measure(line.id,start-timedelta(hours=1),end)['hours'] is None
    total=runtime.stand_runtime(stand,[installation],now=end)
    assert total['lifetime_hours'] is None and total['lifetime_complete'] is False
    assert total['measured_lifetime_hours']==8 and total['measured_history_complete'] is True

def test_runtime_whitespace_correction_reason_rejected_before_lookup(db):
    with pytest.raises(HTTPException) as error:
        correct_event(999,Correction(state='RUNNING',correction_reason='   '),db,SimpleNamespace(id=1,role_id=1))
    assert error.value.status_code==400

def test_preparation_deducts_new_stock_once_and_preserves_identity_on_return(db):
    item,stand,kind,asset,prep=preparation(db)
    at=datetime(2020,1,2)
    result=ComponentLifecycleService(db).finalize_preparation(stand,at,'Operator');db.commit()
    assert result=={'issued':1,'fitted':1} and item.quantity==1
    assert db.query(InventoryTransaction).count()==1
    with pytest.raises(HTTPException):
        ComponentLifecycleService(db).finalize_preparation(stand,at,'Operator')
    assert item.quantity==1 and db.query(InventoryTransaction).count()==1
    stand.current_status=StatusEnum.READY
    returned=ComponentLifecycleService(db).return_components(stand,at+timedelta(hours=1));db.commit()
    assert returned['returned']==1 and returned['new_stock_added']==0
    assert item.quantity==1 and asset.condition=='REUSED'
    assert stand.current_status==StatusEnum.PENDING and stand.current_location==LocationEnum.WIP
    assert db.query(ComponentFitting).one().removed_at is not None
    with pytest.raises(HTTPException):
        ComponentLifecycleService(db).return_components(stand,at+timedelta(hours=2))

@pytest.mark.parametrize('quantity',[None,0])
def test_unknown_or_insufficient_new_stock_has_no_partial_effect(db,quantity):
    item,stand,kind,asset,prep=preparation(db,quantity=quantity)
    with pytest.raises(HTTPException):
        ComponentLifecycleService(db).finalize_preparation(stand,datetime(2020,1,2),'Operator')
    assert item.quantity==quantity and prep.finalized_at is None
    assert db.query(InventoryTransaction).count()==0 and db.query(ComponentFitting).count()==0
    assert asset.condition=='NEW'

def test_missing_preparation_cannot_bypass_identity_tracking(db):
    stand=StandAsset(code='1A');db.add(stand);db.commit()
    with pytest.raises(HTTPException) as error:
        ComponentLifecycleService(db).finalize_preparation(stand,datetime(2020,1,2),'Operator')
    assert error.value.status_code==400
    prep=StandComponentPreparation(stand_id=stand.id,state='SKIPPED',prepared_by='Operator',notes='  ',created_at=datetime(2020,1,1))
    db.add(prep);db.commit()
    with pytest.raises(HTTPException):
        ComponentLifecycleService(db).finalize_preparation(stand,datetime(2020,1,2),'Operator')
    prep.notes='Existing unidentified components; history incomplete.'
    result=ComponentLifecycleService(db).finalize_preparation(stand,datetime(2020,1,2),'Operator')
    assert result['tracking']=='SKIPPED' and result['issued']==0

def test_reused_component_keeps_measured_life_and_unknown_prior_across_stands(db):
    item,stand,kind,asset,prep=preparation(db,condition='REUSED',prior=None)
    start=datetime(2020,1,1);end=start+timedelta(hours=10)
    line=Line(name='W1');db.add(line);db.flush()
    position=Position(line_id=line.id,position_number=1);db.add(position);db.flush()
    db.add_all([LineRuntimeEvent(line_id=line.id,state='RUNNING',event_at=start,recorded_by='Operator'),
        LineRuntimeEvent(line_id=line.id,state='STOPPED',event_at=start+timedelta(hours=8),recorded_by='Operator'),
        LineRuntimeEvent(line_id=line.id,state='RUNNING',event_at=end,recorded_by='Operator')])
    db.add(StandInstallation(stand_id=stand.id,position_id=position.id,installed_at=start,removed_at=end))
    db.commit()
    ComponentLifecycleService(db).finalize_preparation(stand,start,'Operator');db.commit()
    before=ComponentLifecycleService(db).asset_life(asset,at=end)
    assert before['known_runtime_hours']==8 and before['measured_life_hours'] is None
    ComponentLifecycleService(db).return_components(stand,end);db.commit()
    next_stand=StandAsset(code='1B');db.add(next_stand);db.flush()
    next_prep=StandComponentPreparation(stand_id=next_stand.id,state='SAVED',prepared_by='Operator',created_at=end)
    db.add(next_prep);db.flush()
    db.add_all([StandComponentPreparationItem(preparation_id=next_prep.id,component_type_id=kind.id,new_qty=0,reused_qty=1),
        PreparationAssetSelection(preparation_id=next_prep.id,component_type_id=kind.id,asset_id=asset.id),
        StandInstallation(stand_id=next_stand.id,position_id=position.id,installed_at=end,removed_at=end+timedelta(hours=2))])
    db.commit()
    ComponentLifecycleService(db).finalize_preparation(next_stand,end,'Operator');db.commit()
    after=ComponentLifecycleService(db).asset_life(asset,at=end+timedelta(hours=2))
    assert after['known_runtime_hours']==10 and after['measured_life_hours'] is None
    assert item.quantity==2 and db.query(InventoryTransaction).count()==0
    assert db.query(ComponentFitting).filter_by(asset_id=asset.id).count()==2

def test_asset_cache_does_not_hide_later_asset_fittings(db):
    item,stand,kind,first,prep=preparation(db,condition='REUSED',prior=0)
    second=ComponentAsset(code='BR-002',component_type_id=kind.id,condition='REUSED',prior_life_hours=0,created_at=datetime(2020,1,1))
    db.add(second);db.flush()
    db.add(ComponentFitting(asset_id=second.id,stand_id=stand.id,preparation_id=prep.id,fitted_at=datetime(2020,1,1)))
    db.commit()
    service=ComponentLifecycleService(db)
    assert service.asset_payload(first)['current_stand_id'] is None
    assert service.asset_payload(second)['current_stand_id']==stand.id
