from datetime import datetime, timedelta
from types import SimpleNamespace
import importlib.util
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.operations import Operations

import app.models
from app.database.session import Base
from app.models.enums import StatusEnum, LocationEnum
from app.models.line import Line
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.services.operation_service import OperationService


@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    # Match production's partial active-installation indexes in SQLite.
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            predicate = index.dialect_options['postgresql'].get('where')
            if predicate is not None:
                index.dialect_options['sqlite']['where'] = predicate
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def running_stand(db):
    line = Line(name='W1')
    db.add(line)
    db.flush()
    position = Position(line_id=line.id, position_number=1)
    db.add(position)
    db.flush()
    stand = StandAsset(code='1A', current_status=StatusEnum.INSTALLED,
                       current_location=LocationEnum.WRM_LINE, current_position_id=position.id)
    db.add(stand)
    db.flush()
    db.add(StandInstallation(stand_id=stand.id, position_id=position.id,
                            installed_at=datetime.utcnow() - timedelta(hours=5)))
    db.commit()
    return stand, position


def test_new_stand_defaults_to_pending_and_legacy_status_is_blocked(db):
    stand = StandAsset(code='1B')
    db.add(stand)
    db.commit()
    assert stand.current_status == StatusEnum.PENDING
    with pytest.raises(HTTPException):
        OperationService(db).update_preparation_status('1B', StatusEnum.YET_TO_READY, None, 'Operator')
    stand.current_status = StatusEnum.YET_TO_READY
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_removal_returns_stand_to_pending_and_closes_campaign(db):
    stand, _ = running_stand(db)
    OperationService(db).remove_stand(stand.code, None, 'Operator', 'Maintenance')
    assert stand.current_status == StatusEnum.PENDING
    assert stand.current_location == LocationEnum.WIP
    assert stand.current_position_id is None
    assert stand.lifetime_hours == 0
    assert db.query(StandInstallation).one().campaign_hours is None
    assert db.query(StandInstallation).one().removed_at is not None


@pytest.mark.parametrize("replacement_id", [None, 0])
def test_replacement_returns_old_stand_to_pending(db, replacement_id):
    old, position = running_stand(db)
    replacement = StandAsset(id=replacement_id, code='1B', current_status=StatusEnum.READY, current_location=LocationEnum.READY_AREA)
    db.add(replacement)
    db.commit()
    payload = SimpleNamespace(position_id=position.id, removed_stand_code='1A', installed_stand_code='1B',
        changed_at=None, changed_by='Operator', reason='Maintenance', leakage=False, vibration=False,
        abnormal_sound=False, removed_condition=None, notes=None)
    OperationService(db).change_stand(payload, None)
    assert old.current_status == StatusEnum.PENDING
    assert old.current_position_id is None
    assert replacement.current_status == StatusEnum.INSTALLED


def test_migration_moves_only_unstarted_and_preserves_audit():
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE stand_assets (id INTEGER PRIMARY KEY, current_status TEXT, current_location TEXT)'))
        connection.execute(text('CREATE TABLE stand_preparation_events (stand_id INTEGER, from_status TEXT, to_status TEXT, updated_by TEXT, remarks TEXT, changed_at DATETIME)'))
        connection.execute(text("INSERT INTO stand_assets VALUES (1, 'YET_TO_READY', 'WIP'), (2, 'INSTALLED', 'WRM_LINE'), (3, 'READY', 'READY_AREA')"))
        path = Path(__file__).parents[1] / 'alembic/versions/20261123_pending_stands.py'
        spec = importlib.util.spec_from_file_location('pending_migration', path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert connection.execute(text('SELECT current_status FROM stand_assets ORDER BY id')).scalars().all() == ['PENDING', 'INSTALLED', 'READY']
        assert connection.execute(text('SELECT from_status, to_status FROM stand_preparation_events')).one() == ('YET_TO_READY', 'PENDING')
        with pytest.raises(IntegrityError):
            connection.execute(text("UPDATE stand_assets SET current_status='YET_TO_READY' WHERE id=1"))


def test_failed_replacement_rolls_back_the_removal(db):
    from sqlalchemy import event
    old, position = running_stand(db)
    replacement = StandAsset(id=0, code='1B', current_status=StatusEnum.READY, current_location=LocationEnum.READY_AREA)
    db.add(replacement); db.commit()
    payload = SimpleNamespace(position_id=position.id, removed_stand_code='1A', installed_stand_code='1B',
        changed_at=None, changed_by='Operator', reason='Maintenance', leakage=False, vibration=False,
        abnormal_sound=False, removed_condition=None, notes=None)
    def fail_insert(*args):
        raise IntegrityError('simulated insert conflict', {}, Exception('conflict'))
    event.listen(StandInstallation, 'before_insert', fail_insert)
    try:
        with pytest.raises(HTTPException):
            OperationService(db).change_stand(payload, None)
    finally:
        event.remove(StandInstallation, 'before_insert', fail_insert)
    db.refresh(old); db.refresh(replacement)
    assert old.current_status == StatusEnum.INSTALLED
    assert old.current_position_id == position.id
    assert replacement.current_status == StatusEnum.READY
    assert replacement.current_position_id is None
    assert db.query(StandInstallation).one().removed_at is None
