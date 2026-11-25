from datetime import date, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import io
import zipfile
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.database.session import Base
from app.models.user import User
from app.models.pm_activity import PMActivity
from app.models.inventory_item import InventoryItem
from app.models.command_receipt import CommandReceipt
from app.models.stand_asset import StandAsset
from app.models.enums import StatusEnum
from app.api.routes import pm, import_report, knowledge
from app.services.operation_service import OperationService
from app.services.evidence_service import bounded_rows, merge_intervals, in_intervals

@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id=1, username='admin', hashed_password='test-only', role_id=1))
        session.commit()
        yield session
    engine.dispose()

def activity(**overrides):
    return dict(planned_date=datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat(),
        equipment='Stand', activity='Stand changed 7A to 7.1', activity_type='STAND_CHANGE',
        line_name='W1', position_number=7, from_value='7A', to_value='7.1', **overrides)

def test_pm_confirmation_is_history_only_and_idempotent(db, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('PM import must not execute stand changes')
    monkeypatch.setattr(OperationService, 'change_stand', forbidden)
    user = db.get(User, 1)
    payload = pm.ConfirmInput(activities=[activity()], source_text='Reviewed activity')
    key = 'pm-confirm-test-000000001'
    result = pm.confirm_message(payload, db, user, key)
    assert result['saved'] == 1
    assert result['operations'] == []
    assert pm.confirm_message(payload, db, user, key) == result
    assert db.query(PMActivity).count() == 1
    assert db.query(CommandReceipt).count() == 1

def test_pm_invalid_batch_does_not_save_partial_history(db):
    invalid = activity()
    invalid.pop('planned_date')
    payload = pm.ConfirmInput(activities=[activity(), invalid])
    with pytest.raises(HTTPException):
        pm.confirm_message(payload, db, db.get(User, 1), 'pm-invalid-test-000000001')
    assert db.query(PMActivity).count() == 0
    assert db.query(CommandReceipt).count() == 0

def test_backdated_pm_requires_admin_and_completed_future_is_rejected():
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    operator = SimpleNamespace(role_id=2)
    backdated = pm.PMInput(planned_date=today-timedelta(days=1), equipment='Stand', activity='Inspection')
    with pytest.raises(HTTPException) as error:
        pm._check_backdate(backdated, operator)
    assert error.value.status_code == 403
    pm._check_backdate(backdated, SimpleNamespace(role_id=1))
    future = pm.PMInput(planned_date=today+timedelta(days=1), equipment='Stand', activity='Inspection', status='COMPLETED')
    with pytest.raises(HTTPException):
        pm._check_backdate(future, SimpleNamespace(role_id=1))

def test_confidence_zero_and_nonfinite_values_cannot_bypass_review():
    state, _ = import_report.validate_action(None, {'type':'STAND_STATUS','confidence':0})
    assert state == 'REVIEW'
    for confidence in [float('nan'), float('inf'), -1, 2]:
        with pytest.raises(ValidationError):
            import_report.ReportAction(type='STAND_STATUS', confidence=confidence)

def test_report_batch_rolls_back_later_execution_failure(db, monkeypatch):
    db.add_all([StandAsset(code='1A', current_status=StatusEnum.PENDING),
                StandAsset(code='1B', current_status=StatusEnum.PENDING)])
    db.commit()
    monkeypatch.setattr(import_report, 'validate_action', lambda *args: ('SAFE','reviewed'))
    class FailingService:
        def __init__(self, session, auto_commit):
            assert auto_commit is False
            self.db = session
        def update_preparation_status(self, code, *args):
            if code == '1B':
                raise HTTPException(409, 'Conflicting second action')
            self.db.add(InventoryItem(name='must-rollback', quantity=1))
            self.db.flush()
            return {'ok':True}
    monkeypatch.setattr(import_report, 'OperationService', FailingService)
    payload = import_report.ConfirmInput(actions=[
        import_report.ReportAction(type='STAND_STATUS',confidence=.99,stand=code,status='READY',done_by='Admin')
        for code in ['1A','1B']])
    with pytest.raises(HTTPException):
        import_report.confirm_report(payload, db, db.get(User,1), 'report-confirm-test-000000001')
    assert db.query(InventoryItem).count() == 0
    assert db.query(CommandReceipt).count() == 0

def test_report_review_only_action_never_executes(db, monkeypatch):
    monkeypatch.setattr(import_report, 'OperationService', lambda *args, **kwargs: pytest.fail('No writes permitted'))
    payload = import_report.ConfirmInput(actions=[
        import_report.ReportAction(type='ENTRY_GUIDE_SUMMARY',confidence=.2,position=2)])
    with pytest.raises(HTTPException):
        import_report.confirm_report(payload, db, db.get(User,1), 'report-review-test-000000001')
    assert db.query(CommandReceipt).count() == 0

def test_parsers_do_not_invent_dates_and_report_time_is_plant_local():
    parsed = pm.fallback('Stand changed from 7A to 7.1')
    assert parsed and parsed[0]['planned_date'] is None
    instant, error = import_report._parse_changed_at({'date':'25/11/2026','time':'12:00'})
    assert error is None
    assert instant.utcoffset() == timedelta(hours=5,minutes=30)

def test_archive_and_text_limits_are_enforced(monkeypatch):
    monkeypatch.setattr(knowledge, 'MAX_TEXT', 10)
    with pytest.raises(HTTPException):
        knowledge._extract_text('file.txt', b'x'*11)
    monkeypatch.setattr(knowledge, 'MAX_EXPANDED', 10)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('large.xml', 'x'*11)
    with pytest.raises(HTTPException):
        knowledge._extract_text('file.docx', payload.getvalue())

def test_evidence_bounds_and_centuries_long_intervals_remain_compact():
    class Query:
        def limit(self, limit):
            self.limit_value = limit
            return self
        def all(self):
            return list(range(self.limit_value))
    rows, truncated = bounded_rows(Query(), 3)
    assert rows == [0,1,2] and truncated
    windows = merge_intervals([(date(1900,1,1),date(9998,1,1)),
        (date(2000,1,1),date(2001,1,1))])
    assert len(windows) == 1
    assert in_intervals(date(1900,1,1), windows)
    assert in_intervals(date(9998,1,1), windows)
    assert not in_intervals(date(1899,1,1), windows)
