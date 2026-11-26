from datetime import datetime, date, timedelta
from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.database.session import Base
from app.models.line import Line
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.stand_installation import StandInstallation
from app.models.line_runtime import LineRuntimeEvent
from app.models.enums import StatusEnum, LocationEnum
from app.models.reliability_history import HistoricalCampaign
from app.services.runtime_service import RuntimeService
from app.services.dashboard_service import DashboardService
from app.services.stand_service import StandService
from app.services.life_insight_service import LifeInsightService, completed_comparisons, dedupe_completed_campaigns

NOW=datetime(2026,11,26,12)

@pytest.fixture
def db():
    engine=create_engine('sqlite:///:memory:')
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            predicate=index.dialect_options['postgresql'].get('where')
            if predicate is not None:
                index.dialect_options['sqlite']['where']=predicate
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def current(db, code='1A', installed=None, line_name='W1'):
    line=Line(name=line_name);db.add(line);db.flush()
    position=Position(line_id=line.id,position_number=1);db.add(position);db.flush()
    stand=StandAsset(code=code,current_status=StatusEnum.INSTALLED,current_location=LocationEnum.WRM_LINE,current_position_id=position.id)
    db.add(stand);db.flush()
    installation=StandInstallation(stand_id=stand.id,position_id=position.id,installed_at=installed or NOW-timedelta(days=4))
    db.add(installation);db.commit()
    return line,position,stand,installation


def event(db,line,at,state):
    db.add(LineRuntimeEvent(line_id=line.id,event_at=at,state=state,recorded_by='Operator',reason='Measured line state'))
    db.commit()


def test_no_runtime_is_unknown_with_elapsed_age_and_no_false_zero(db):
    line,position,stand,installation=current(db)
    value=RuntimeService(db).installation(installation,NOW)
    assert value['hours'] is None and value['coverage_status']=='NONE'
    assert value['has_coverage'] is False and value['elapsed_hours']==96
    dashboard=DashboardService(db).get_plant_dashboard()[0]['positions'][0]['current_stand']
    assert dashboard['campaign_hours'] is None and dashboard['known_runtime_hours'] is None
    detail=StandService(db).get_stand_details(stand.id)
    assert detail['known_runtime_hours'] is None and detail['history'][0]['known_runtime_hours'] is None
    assert detail['measured_lifetime_hours'] is None


def test_complete_recorded_zero_remains_actual_zero(db):
    line,position,stand,installation=current(db)
    event(db,line,installation.installed_at,'STOPPED')
    value=RuntimeService(db).installation(installation,NOW)
    assert value['hours']==0 and value['complete'] is True
    assert value['coverage_status']=='COMPLETE' and value['known_hours']==0
    row=LifeInsightService(db).summary(NOW)['longest_current_measured']
    assert row['actual_runtime_hours']==0 and row['elapsed_hours']==96


def test_partial_stopped_observation_is_zero_observed_not_full_zero(db):
    line,position,stand,installation=current(db)
    event(db,line,installation.installed_at+timedelta(hours=2),'STOPPED')
    value=RuntimeService(db).installation(installation,NOW)
    assert value['hours'] is None and value['known_hours']==0
    assert value['coverage_status']=='PARTIAL' and value['has_coverage']
    assert value['covered_elapsed_hours']==94


def test_start_stop_boundaries_exclude_downtime(db):
    start=NOW-timedelta(hours=10)
    line,position,stand,installation=current(db,installed=start)
    event(db,line,start,'RUNNING');event(db,line,start+timedelta(hours=4),'STOPPED');event(db,line,start+timedelta(hours=6),'RUNNING')
    value=RuntimeService(db).installation(installation,NOW)
    assert value['hours']==8 and value['elapsed_hours']==10


def test_longest_elapsed_and_measured_are_distinct_ongoing_rankings(db):
    old,_,_,installation=current(db,'1A',NOW-timedelta(days=4),'W1')
    new,_,_,new_inst=current(db,'1B',NOW-timedelta(days=2),'W2')
    event(db,old,NOW-timedelta(days=1),'RUNNING')
    event(db,new,new_inst.installed_at,'RUNNING')
    data=LifeInsightService(db).summary(NOW)
    assert data['longest_current_installation']['stand']=='1A'
    assert data['longest_current_measured']['stand']=='1B'
    assert data['completed_campaigns']==0 and data['historical_stand_performance']==[]
    assert all(row['ongoing'] for row in data['ongoing'])


def snapshot(code='1A', line='W1', pos=1, days=10, start=date(2026,1,1)):
    return SimpleNamespace(stand_code=code,line_name=line,position_number=pos,life_days=days,installed_date=start,removed_date=start+timedelta(days=days))


def test_snapshot_dedupes_and_excludes_incomplete_invalid_and_conflicting():
    good=snapshot();duplicate=snapshot()
    conflicting=snapshot('1B');conflict=snapshot('1B',days=12)
    ongoing=snapshot('1C');ongoing.removed_date=None
    invalid=snapshot('1D');invalid.life_days=500
    rows,excluded=dedupe_completed_campaigns([good,duplicate,conflicting,conflict,ongoing,invalid],NOW)
    assert rows==[good]
    assert excluded==dict(ongoing=1,invalid=1,duplicate=1,conflicting=2)


def test_historical_plant_day_is_india_date_not_utc_midnight():
    row=snapshot(days=1,start=date(2026,11,25))
    assert dedupe_completed_campaigns([row],datetime(2026,11,25,20))[0]==[row]


def test_peers_exclude_subject_and_keep_same_position_context():
    rows=[snapshot('1A',days=20) for _ in range(3)]+[snapshot('1B',days=10) for _ in range(3)]
    rows += [snapshot('1C',line='W2',days=10) for _ in range(3)]
    rows += [snapshot('2A',line='W2',pos=2,days=1000) for _ in range(3)]
    stands,positions=completed_comparisons(rows)
    a=next(row for row in stands if row['stand']=='1A')
    assert a['peer_campaigns']==3 and a['peer_median_days']==10 and a['vs_peer_pct']==100
    weak=next(row for row in positions if row['line']=='W2' and row['position']==1)
    assert weak['peer_campaigns']==6 and weak['peer_median_days']==15 and weak['vs_peer_pct']==-33.3
    assert next(row for row in positions if row['position']==2)['evidence']=='INSUFFICIENT'


def test_new_registered_completed_campaigns_use_measured_hours_separately(db):
    line=Line(name='W1');db.add(line);db.flush()
    pos=Position(line_id=line.id,position_number=1);db.add(pos);db.flush()
    a,b=StandAsset(code='1A'),StandAsset(code='1B');db.add_all([a,b]);db.flush()
    start=NOW-timedelta(days=5)
    for i in range(6):
        begin=start+timedelta(hours=i*12)
        asset=a if i<3 else b
        hours=8 if i<3 else 4
        db.add(StandInstallation(stand_id=asset.id,position_id=pos.id,installed_at=begin,removed_at=begin+timedelta(hours=hours)))
    db.add(LineRuntimeEvent(line_id=line.id,event_at=start,state='RUNNING',recorded_by='Operator',reason='Measured'))
    db.add(HistoricalCampaign(line_name='W1',position_number=1,stand_code='1Z',installed_date=date(2026,1,1),removed_date=date(2026,1,11),life_days=10,source_file='snapshot.xlsx'))
    db.commit()
    data=LifeInsightService(db).summary(NOW)
    assert data['measured_completed_campaigns']==6 and data['completed_campaigns']==1
    best=data['measured_completed_stand_performance'][0]
    assert best['stand']=='1A' and best['median_hours']==8 and best['vs_peer_pct']==100
    assert best['basis']=='MEASURED_MILL_RUNTIME_HOURS'
    assert data['historical_stand_performance'][0]['median_days']==10
