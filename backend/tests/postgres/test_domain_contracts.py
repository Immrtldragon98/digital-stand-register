"""Release evidence that must run against PostgreSQL, never a production URL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import threading
import time

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.command_receipt import CommandReceipt
from app.models.component_asset import ComponentAsset, ComponentFitting, PreparationAssetSelection
from app.models.enums import StatusEnum, LocationEnum
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.models.line import Line
from app.models.line_runtime import LineRuntimeEvent
from app.models.stand_asset import StandAsset
from app.models.stand_component import StandComponentPreparation, StandComponentPreparationItem, StandComponentType
from app.models.stand_installation import StandInstallation
from app.models.stand_position import Position
from app.models.user import User
from app.services.command_service import run_command
from app.services.component_lifecycle_service import ComponentLifecycleService
from app.services.runtime_service import RuntimeService


def test_runtime_uses_recorded_running_intervals_not_elapsed_or_planned_pm(pg_engine):
    start = datetime(2026, 11, 1)
    with Session(pg_engine) as db:
        line = Line(name='QA-RUNTIME'); db.add(line); db.flush()
        db.add_all([
            LineRuntimeEvent(line_id=line.id, state='RUNNING', event_at=start, recorded_by='QA'),
            LineRuntimeEvent(line_id=line.id, state='STOPPED', event_at=start+timedelta(hours=4), recorded_by='QA', reason='Recorded PM'),
            LineRuntimeEvent(line_id=line.id, state='RUNNING', event_at=start+timedelta(hours=6), recorded_by='QA'),
        ])
        db.commit()
        service = RuntimeService(db)
        measured = service.measure(line.id, start, start+timedelta(hours=10))
        assert measured['hours'] == 8
        assert measured['known_hours'] == 8
        assert measured['elapsed_hours'] == 10
        assert measured['complete'] is True
        partial = service.measure(line.id, start-timedelta(hours=3), start+timedelta(hours=10))
        assert partial['hours'] is None
        assert partial['known_hours'] == 8
        assert partial['complete'] is False


def test_concurrent_same_command_key_commits_one_outcome_and_one_effect(pg_engine):
    with Session(pg_engine) as db:
        user = User(username='QA-command', hashed_password='test-only-hash', role_id=1)
        db.add(user); db.commit(); user_id = user.id
    barrier = threading.Barrier(2)
    callbacks = []
    counter_lock = threading.Lock()
    key = 'qa-concurrent-change-000001'
    def submit(_):
        with Session(pg_engine) as db:
            barrier.wait(timeout=10)
            def action():
                with counter_lock:
                    callbacks.append(1)
                time.sleep(0.05)
                db.add(InventoryItem(name='QA command effect', quantity=4))
                return {'status': 'saved', 'quantity': 4}
            return run_command(db, user_id, key, 'QA_COMMAND', {'quantity': 4}, action)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [1, 2]))
    assert results == [{'status': 'saved', 'quantity': 4}] * 2
    assert len(callbacks) == 1
    with Session(pg_engine) as db:
        assert db.query(InventoryItem).filter_by(name='QA command effect').count() == 1
        assert db.query(CommandReceipt).filter_by(user_id=user_id, request_key=key).count() == 1
        with pytest.raises(HTTPException) as conflict:
            run_command(db, user_id, key, 'QA_COMMAND', {'quantity': 9}, lambda: pytest.fail('Payload mismatch must not run'))
        assert conflict.value.status_code == 409


def preparation(db, stock_quantity):
    now = datetime(2026, 11, 1)
    stock = InventoryItem(name='QA Preparation Bearing', quantity=stock_quantity)
    stand = StandAsset(code='2-QA', current_status=StatusEnum.PENDING, current_location=LocationEnum.WIP)
    db.add_all([stock, stand]); db.flush()
    kind = StandComponentType(name='QA Bearing', active=True, required_qty=1, inventory_item_id=stock.id)
    db.add(kind); db.flush()
    asset = ComponentAsset(code='QA-BRG-001', component_type_id=kind.id, condition='NEW', prior_life_hours=0, created_at=now)
    prep = StandComponentPreparation(stand_id=stand.id, state='SAVED', prepared_by='QA', created_at=now)
    db.add_all([asset, prep]); db.flush()
    prep.items.append(StandComponentPreparationItem(component_type_id=kind.id, new_qty=1, reused_qty=0))
    db.add(PreparationAssetSelection(preparation_id=prep.id, component_type_id=kind.id, asset_id=asset.id))
    db.commit()
    return stock.id, stand.id, asset.id, prep.id


def test_preparation_issues_verified_stock_and_fits_identity_only_once(pg_engine):
    with Session(pg_engine) as db:
        stock_id, stand_id, asset_id, prep_id = preparation(db, 1)
        stand = db.get(StandAsset, stand_id)
        result = ComponentLifecycleService(db).finalize_preparation(stand, datetime(2026, 11, 1, 1), 'QA')
        assert result == {'issued': 1, 'fitted': 1}
        db.commit()
        # A direct duplicate may be rejected or acknowledged as a no-op. Neither
        # path may consume stock again or create another fitting/transaction.
        try:
            ComponentLifecycleService(db).finalize_preparation(stand, datetime(2026, 11, 1, 1), 'QA')
            db.commit()
        except HTTPException as error:
            assert error.status_code in (400, 409)
            db.rollback()
        assert db.get(InventoryItem, stock_id).quantity == 0
        assert db.query(InventoryTransaction).filter_by(item_id=stock_id).count() == 1
        fitting = db.query(ComponentFitting).filter_by(asset_id=asset_id).one()
        assert fitting.preparation_id == prep_id
        assert fitting.removed_at is None
        assert db.get(ComponentAsset, asset_id).condition == 'REUSED'


@pytest.mark.parametrize('quantity', [None, 0])
def test_unknown_or_insufficient_stock_never_partially_fits_components(pg_engine, quantity):
    with Session(pg_engine) as db:
        stock_id, stand_id, asset_id, prep_id = preparation(db, quantity)
        with pytest.raises(HTTPException) as rejected:
            ComponentLifecycleService(db).finalize_preparation(db.get(StandAsset, stand_id), datetime(2026, 11, 1, 1), 'QA')
        assert rejected.value.status_code in (400, 409)
        db.rollback()
        assert db.get(InventoryItem, stock_id).quantity == quantity
        assert db.query(InventoryTransaction).filter_by(item_id=stock_id).count() == 0
        assert db.query(ComponentFitting).filter_by(asset_id=asset_id).count() == 0
        assert db.get(StandComponentPreparation, prep_id).finalized_at is None
        assert db.get(ComponentAsset, asset_id).condition == 'NEW'


def test_reused_identity_accumulates_measured_life_across_two_stands(pg_engine):
    start = datetime(2026, 11, 1)
    with Session(pg_engine) as db:
        line = Line(name='QA-REUSE'); db.add(line); db.flush()
        position = Position(line_id=line.id, position_number=2); db.add(position); db.flush()
        kind = StandComponentType(name='QA reused shaft', active=True)
        stands = [StandAsset(code='2-QA-A'), StandAsset(code='2-QA-B')]
        db.add_all([kind, *stands]); db.flush()
        asset = ComponentAsset(code='QA-SHAFT-001', component_type_id=kind.id, condition='REUSED', prior_life_hours=5, created_at=start)
        db.add(asset); db.flush()
        db.add(LineRuntimeEvent(line_id=line.id, state='RUNNING', event_at=start, recorded_by='QA'))
        for stand, begin, end in [(stands[0], 0, 2), (stands[1], 3, 7)]:
            prep = StandComponentPreparation(stand_id=stand.id, state='FINALIZED', prepared_by='QA', created_at=start+timedelta(hours=begin), finalized_at=start+timedelta(hours=begin))
            db.add(prep); db.flush()
            db.add(ComponentFitting(asset_id=asset.id, stand_id=stand.id, preparation_id=prep.id,
                fitted_at=start+timedelta(hours=begin), removed_at=start+timedelta(hours=end)))
            db.add(StandInstallation(stand_id=stand.id, position_id=position.id,
                installed_at=start+timedelta(hours=begin), removed_at=start+timedelta(hours=end)))
        db.commit()
        life = ComponentLifecycleService(db).asset_life(asset, at=start+timedelta(hours=8))
        assert life['known_runtime_hours'] == 6
        assert life['measured_life_hours'] == 11
        assert life['life_complete'] is True
        # An unknown pre-register baseline cannot become certified merely
        # because the newly recorded campaigns have complete runtime coverage.
        asset.prior_life_hours = None; db.commit()
        unknown = ComponentLifecycleService(db).asset_life(asset, at=start+timedelta(hours=8))
        assert unknown['known_runtime_hours'] == 6
        assert unknown['measured_life_hours'] is None
        assert unknown['life_complete'] is False


def test_operator_cannot_backdate_a_swap_or_reset_preparation(pg_engine):
    from types import SimpleNamespace
    from app.services.operation_service import OperationService
    with Session(pg_engine) as db:
        user = User(username='QA-operator', hashed_password='test-only-hash', role_id=2)
        line = Line(name='QA-ROLE'); db.add_all([user, line]); db.flush()
        position = Position(line_id=line.id, position_number=3); db.add(position); db.flush()
        old = StandAsset(code='3-QA-OLD', current_status=StatusEnum.INSTALLED, current_location=LocationEnum.WRM_LINE, current_position_id=position.id)
        new = StandAsset(code='3-QA-NEW', current_status=StatusEnum.READY, current_location=LocationEnum.READY_AREA)
        db.add_all([old,new]); db.flush()
        db.add(StandInstallation(stand_id=old.id, position_id=position.id, installed_at=datetime.utcnow()-timedelta(hours=2)))
        db.commit()
        payload = SimpleNamespace(position_id=position.id, removed_stand_code=old.code, installed_stand_code=new.code,
            changed_at=datetime.utcnow()-timedelta(hours=1), changed_by='QA-operator', reason='Correction',
            leakage=False, vibration=False, abnormal_sound=False, removed_condition=None, notes=None)
        with pytest.raises(HTTPException) as backdate:
            OperationService(db).change_stand(payload, user.id)
        assert backdate.value.status_code == 403
        db.rollback()
        with pytest.raises(HTTPException) as reset:
            OperationService(db).update_preparation_status(new.code, StatusEnum.PENDING, user.id, user.username, 'Correction')
        assert reset.value.status_code == 403
        db.rollback()
        db.refresh(old); db.refresh(new)
        assert old.current_status == StatusEnum.INSTALLED
        assert new.current_status == StatusEnum.READY
        assert db.query(StandInstallation).count() == 1
