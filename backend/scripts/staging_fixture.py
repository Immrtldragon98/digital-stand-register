"""Seed an empty, isolated staging database; never modify a production database."""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy.engine import make_url


def validate_target(url, environment):
    if environment!='staging' or not (make_url(url).database or '').endswith('_staging'):
        raise RuntimeError('Staging requires its own database ending in _staging.')


def seed(db):
    from app.models.line import Line
    from app.models.stand_position import Position
    from app.models.stand_asset import StandAsset
    from app.models.stand_installation import StandInstallation
    from app.models.line_runtime import LineRuntimeEvent
    from app.models.inventory_item import InventoryItem
    from app.models.enums import StatusEnum,LocationEnum
    existing=db.query(Line).all()
    if existing:
        if any(not line.name.startswith('DEMO-') for line in existing):raise RuntimeError('Refusing non-synthetic staging data.')
        return
    now=datetime.utcnow()
    for index in [1,2]:
        line=Line(name=f'DEMO-W{index}');db.add(line);db.flush()
        for number in [1,2,3]:
            position=Position(line_id=line.id,position_number=number);db.add(position);db.flush()
            stand=StandAsset(code=f'DEMO-{index}-{number}A',current_status=StatusEnum.INSTALLED,current_location=LocationEnum.WRM_LINE,current_position_id=position.id,condition_notes='Synthetic staging fixture, not plant evidence.')
            db.add(stand);db.flush()
            db.add(StandInstallation(stand_id=stand.id,position_id=position.id,installed_at=now-timedelta(hours=48),installed_by='Synthetic fixture'))
        db.add(LineRuntimeEvent(line_id=line.id,state='RUNNING',event_at=now-timedelta(hours=48),recorded_by='Synthetic fixture',reason='Synthetic staging data'))
    db.add(StandAsset(code='DEMO-PREP-1',current_status=StatusEnum.PENDING))
    db.add(InventoryItem(name='DEMO bearing',quantity=4,minimum_quantity=8,remarks='Synthetic staging stock'))
    db.add(InventoryItem(name='DEMO seal',quantity=None,minimum_quantity=2,remarks='Synthetic unverified balance'))
    db.commit()


if __name__=='__main__':
    from app.config.settings import settings
    validate_target(settings.DATABASE_URL,os.getenv('DSR_ENVIRONMENT'))
    if '--validate-only' not in sys.argv:
        import app.models
        from app.database.session import SessionLocal
        with SessionLocal() as db:seed(db)
    print('Isolated staging database verified; synthetic fixtures only.')
