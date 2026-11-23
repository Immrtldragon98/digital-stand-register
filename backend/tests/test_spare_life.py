from types import SimpleNamespace
import importlib.util
import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
import app.models
from app.database.session import Base
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.models.spare_life_record import SpareLifeRecord
from app.services.spare_life_service import life_summaries, life_summary
from app.schemas.inventory import SpareLifeInput, InventorySetQuantity, InventoryQuantityChange
from app.api.routes.inventory import list_inventory, record_spare_life, set_quantity, change_quantity

@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_weighted_completed_life_overrides_manual_and_does_not_change_stock(db):
    item = InventoryItem(name='Bearing', quantity=8, observed_avg_life_hours=9999, expected_life_hours=100)
    db.add(item); db.commit()
    user = SimpleNamespace(username='Operator')
    record_spare_life(item.id, SpareLifeInput(life_hours=100, quantity=3), db, user)
    summary = record_spare_life(item.id, SpareLifeInput(life_hours=300, quantity=1), db, user)
    assert summary['average_life_hours'] == 150
    assert summary['life_sample_count'] == 4
    assert item.quantity == 8
    output = list_inventory(False, db)[0]
    assert output['average_life_source'] == 'COMPLETED_RECORDS'
    assert output['reliability_pct'] == 150
    assert output['quantity'] == 8
    assert db.query(InventoryTransaction).count() == 0
    assert db.query(SpareLifeRecord).first().recorded_by == 'Operator'


def test_unknown_life_and_stock_are_not_zero(db):
    item = InventoryItem(name='Seal', minimum_quantity=5)
    db.add(item); db.commit()
    output = list_inventory(False, db)[0]
    assert output['quantity'] is None
    assert output['availability_pct'] is None
    assert output['average_life_hours'] is None
    assert output['average_life_source'] == 'UNKNOWN'
    assert output['life_sample_count'] == 0


def test_manual_average_is_labelled_without_invented_samples(db):
    item = InventoryItem(name='Roller', observed_avg_life_hours=240)
    db.add(item); db.commit()
    assert life_summary(item, life_summaries(db)) == dict(average_life_hours=240,
        life_sample_count=0, life_record_count=0, average_life_source='MANUAL')


def test_stock_opening_zero_then_receipt_and_issue_are_audited(db):
    item = InventoryItem(name='Seal', minimum_quantity=4)
    db.add(item); db.commit()
    user = SimpleNamespace(username='Operator')
    delta = InventoryQuantityChange(delta=-1, operator='Operator', reason='Issue')
    with pytest.raises(HTTPException):
        change_quantity(item.id, delta, db, user)
    set_quantity(item.id, InventorySetQuantity(quantity=0, operator='Operator', reason='Physical count'), db, user)
    assert list_inventory(False, db)[0]['quantity'] == 0
    assert list_inventory(False, db)[0]['availability_pct'] == 0
    change_quantity(item.id, InventoryQuantityChange(delta=5, operator='Operator', reason='Receipt'), db, user)
    change_quantity(item.id, delta, db, user)
    assert item.quantity == 4
    assert db.query(InventoryTransaction).order_by(InventoryTransaction.id).first().quantity_before is None
    assert db.query(InventoryTransaction).count() == 3
    with pytest.raises(HTTPException):
        change_quantity(item.id, InventoryQuantityChange(delta=-10, operator='Operator', reason='Issue'), db, user)
    assert item.quantity == 4


def test_life_input_rejects_invalid_samples():
    for kwargs in [{'life_hours':0}, {'life_hours':-1}, {'life_hours':float('nan')}, {'life_hours':float('inf')}, {'life_hours':10,'quantity':0}]:
        with pytest.raises(ValueError):
            SpareLifeInput(**kwargs)


def test_migration_catalog_keeps_stock_unknown_and_preserves_existing_items():
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE inventory_items (id INTEGER PRIMARY KEY, name TEXT UNIQUE, quantity INTEGER NOT NULL, minimum_quantity INTEGER, location TEXT, criticality TEXT, is_active BOOLEAN)'))
        connection.execute(text('CREATE TABLE inventory_transactions (id INTEGER PRIMARY KEY, quantity_before INTEGER NOT NULL)'))
        connection.execute(text('CREATE TABLE activity_logs (id INTEGER PRIMARY KEY, timestamp DATETIME, action TEXT, details TEXT)'))
        connection.execute(text("INSERT INTO inventory_items VALUES (1, 'Bearing', 7, 1, 'Store', 'LOW', true)"))
        payload = dict(plans=[dict(rows=[dict(name='Bearing'),dict(name='Seal')])], usage_summary=[dict(name='Seal')])
        connection.execute(text("INSERT INTO activity_logs VALUES (1, CURRENT_TIMESTAMP, 'SPARE_WORKBOOK_IMPORT', :data)"), {'data':json.dumps(payload)})
        path = Path(__file__).parents[1] / 'alembic/versions/20261123_spare_life.py'
        spec = importlib.util.spec_from_file_location('life_migration', path)
        migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
        migration.op = Operations(MigrationContext.configure(connection)); migration.upgrade()
        assert connection.execute(text('SELECT name, quantity FROM inventory_items ORDER BY name')).all() == [('Bearing',7),('Seal',None)]
