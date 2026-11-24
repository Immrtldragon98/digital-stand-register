from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from types import SimpleNamespace
import threading
import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import app.models
from app.models.line import Line
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.models.enums import StatusEnum, LocationEnum
from app.models.user import User
from app.schemas.inventory import InventoryQuantityChange
from app.api.routes.inventory import change_quantity
from app.services.operation_service import OperationService


def test_migrations_reach_single_head(pg_engine):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    config = Config('alembic.ini')
    head = ScriptDirectory.from_config(config).get_current_head()
    with pg_engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == head


def test_lower_id_replacement_releases_unique_position_atomically(pg_engine):
    with Session(pg_engine) as db:
        line = Line(name='QA-W1'); db.add(line); db.flush()
        position = Position(line_id=line.id, position_number=7); db.add(position); db.flush()
        old = StandAsset(id=200, code='7A', current_status=StatusEnum.INSTALLED, current_location=LocationEnum.WRM_LINE, current_position_id=position.id)
        replacement = StandAsset(id=100, code='7.1', current_status=StatusEnum.READY, current_location=LocationEnum.READY_AREA)
        db.add_all([old, replacement]); db.flush()
        db.add(StandInstallation(stand_id=old.id, position_id=position.id, installed_at=datetime.utcnow()-timedelta(hours=4)))
        db.commit()
        payload = SimpleNamespace(position_id=position.id, removed_stand_code=old.code, installed_stand_code=replacement.code, changed_at=None, changed_by='QA', reason='Test', leakage=False, vibration=False, abnormal_sound=False, removed_condition=None, notes=None)
        OperationService(db).change_stand(payload, None)
        assert old.current_status == StatusEnum.PENDING
        assert old.current_position_id is None
        assert replacement.current_position_id == position.id
        assert db.query(StandInstallation).filter(StandInstallation.removed_at.is_(None)).count() == 1


def test_database_rejects_two_active_installations(pg_engine):
    with Session(pg_engine) as db:
        line = Line(name='QA-W1'); db.add(line); db.flush()
        position = Position(line_id=line.id, position_number=1); db.add(position); db.flush()
        stands = [StandAsset(code='1A'), StandAsset(code='1B')]; db.add_all(stands); db.flush()
        for stand in stands:
            db.add(StandInstallation(stand_id=stand.id, position_id=position.id))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_two_users_cannot_issue_the_same_last_spare(pg_engine):
    with Session(pg_engine) as db:
        item = InventoryItem(name='QA Bearing', quantity=1); db.add(item); db.commit(); item_id=item.id
    start = threading.Barrier(2)
    def issue(operator):
        with Session(pg_engine) as db:
            start.wait()
            try:
                change_quantity(item_id, InventoryQuantityChange(delta=-1, operator=operator, reason='QA issue'), db, SimpleNamespace(username=operator))
                return 'saved'
            except HTTPException as error:
                db.rollback()
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(issue, ['QA1', 'QA2']))
    assert results.count('saved') == 1
    assert results.count(400) == 1
    with Session(pg_engine) as db:
        assert db.get(InventoryItem,item_id).quantity == 0
        assert db.query(InventoryTransaction).filter_by(item_id=item_id).count() == 1
