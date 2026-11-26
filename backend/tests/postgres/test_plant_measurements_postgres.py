from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.stand_asset import StandAsset
from app.models.enums import StatusEnum
from app.models.plant_measurement import PreparationCycle,MaintenanceMeasurement
from app.api.routes.plant import start_preparation,measure,MeasurementInput

def test_migration_and_concurrent_preparation_and_effort_receipts(pg_engine):
    with Session(pg_engine) as db:
        user=User(username='measurement-test',role_id=2,hashed_password='test-only');stand=StandAsset(code='1A',current_status=StatusEnum.PENDING)
        db.add_all([user,stand]);db.commit();user_id,stand_id=user.id,stand.id
    def start(_):
        with Session(pg_engine) as db:return start_preparation(stand_id,db,db.get(User,user_id))
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(start,range(2)))
    assert rows[0]['id']==rows[1]['id']
    payload=MeasurementInput(request_id=uuid4(),kind='INVESTIGATION',duration_minutes=12,description='Measured investigation effort')
    def record(_):
        with Session(pg_engine) as db:return measure(payload,db,db.get(User,user_id))
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(record,range(2)))
    assert rows[0]==rows[1]
    with Session(pg_engine) as db:
        assert db.query(PreparationCycle).count()==1 and db.query(MaintenanceMeasurement).count()==1
