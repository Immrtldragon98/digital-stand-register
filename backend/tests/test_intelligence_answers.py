from datetime import date
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from app.api.routes.intelligence import completed_snapshot_campaigns, position_screening, IntelligenceQuestion
from app.services.intelligence_answer_service import answer_from_evidence, question_scope


def campaign(line='W1', start=date(2026,1,1), end=date(2026,1,3), life=2):
    return SimpleNamespace(line_name=line, position_number=7, stand_code='7A', installed_date=start, removed_date=end, life_days=life)


def test_closed_only_and_deduplication():
    valid=campaign()
    rows=[valid,campaign(),campaign(end=None,life=99),campaign(end=date(2025,1,1)),campaign(life=float('nan'))]
    assert completed_snapshot_campaigns(rows)==[valid]


def test_independent_peers_and_minimum_samples():
    rows=[campaign(start=date(2026,1,i),end=date(2026,1,i+1),life=1) for i in range(1,4)]
    rows += [campaign(line='W2',start=date(2026,1,i),end=date(2026,1,i+9),life=9) for i in range(1,4)]
    own=next(x for x in position_screening(rows) if x['line']=='W1')
    assert own['peer_campaigns']==3 and own['peer_median_days']==9
    assert own['vs_position_baseline_pct']==-88.9
    assert not any(x['eligible_for_comparison'] for x in position_screening(rows[:-1]))


def insights():
    return {'as_of':'2026-11-26T10:00:00Z','ongoing':[
        {'stand':'7A','line':'W1','position':7,'elapsed_hours':200,'actual_runtime_hours':None,'runtime_complete':False},
        {'stand':'7B','line':'W4','position':7,'elapsed_hours':100,'actual_runtime_hours':20,'runtime_complete':True}],
        'historical_stand_performance':[{'stand':'7A','line':'W1','position':7,'avg_days':9,'median_days':9,'campaigns':1,'peer_campaigns':2,'vs_peer_pct':None,'evidence':'INSUFFICIENT'}], 'weak_positions':[]}


@pytest.mark.parametrize('question',['Which stand is running longest?','Which stand running for more time?'])
def test_longest_elapsed_never_becomes_measured_life(question):
    response=answer_from_evidence(question,insights(),{})
    assert response['intent']=='LONGEST_CURRENT'
    assert '200.00 elapsed calendar h' in response['answer']
    assert 'actual mill-running hours are unknown' in response['answer']
    assert response['provider']=='deterministic'


def test_partial_measurement_does_not_establish_global_winner():
    response=answer_from_evidence('Which stand has longest actual mill-runtime?',insights(),{})
    assert 'W4 P7 · 7B' in response['answer']
    assert 'overall actual-runtime winner cannot be established' in response['answer']
    assert question_scope('Investigate WRM#4 P7')[:2]==('W4',7)


def test_sparse_completed_history_does_not_assert_better():
    response=answer_from_evidence('Which stand has better life at W1 P7?',insights(),{})
    assert response['intent']=='COMPLETED_STAND_COMPARISON'
    assert 'not enough like-for-like evidence' in response['answer']
    assert 'n=1, peer n=2' in response['answer']
    assert response['evidence'][0]['basis']=='INFERRED_SNAPSHOT_ELAPSED_DAYS'


def test_measured_complete_cohorts_preferred_without_unit_mixing():
    data=insights();data['measured_completed_stand_performance']=[{'stand':'7A','line':'W1','position':7,'avg_hours':50,'median_hours':40,'peer_median_hours':20,'campaigns':4,'peer_campaigns':5,'vs_peer_pct':100,'evidence':'SUFFICIENT'}]
    response=answer_from_evidence('Which stand has better life?',data,{})
    assert '40.00 mill-running h' in response['answer']
    assert response['evidence'][0]['basis']=='MEASURED_MILL_RUNTIME_HOURS'
    assert '9.00 elapsed d' not in response['answer']


def test_weak_verdict_requires_support():
    response=answer_from_evidence('Which positions are weaks?',insights(),{})
    assert 'No weak-position conclusion is supported' in response['answer']
    data=insights();data['weak_positions']=[{'line':'W1','position':7,'median_days':2,'peer_median_days':5,'vs_peer_pct':-60,'campaigns':4,'peer_campaigns':5,'evidence':'SUFFICIENT'}]
    response=answer_from_evidence('Weak positions?',data,{})
    assert 'n=4, peer n=5' in response['answer']
    assert 'not a failure diagnosis' in response['answer']


def test_recorded_reasons_are_not_causal_claims():
    response=answer_from_evidence('Why W1 P7 weak?',insights(),{'data':{'process_observations':0},'position_investigation':{'line':'W1','position':7,'campaigns':3,'causes':[{'cause':'BEARING','count':2}],'event_summary':{'count':2,'stoppages':1,'downtime_minutes':10}}})
    assert 'bearing (2)' in response['answer']
    assert 'does not prove a root cause' in response['answer']
    assert 'No process observations are imported' in response['answer']


def test_question_bound():
    with pytest.raises(ValidationError):IntelligenceQuestion(question='a'*1001)


def test_longest_completed_life_is_not_ongoing_age():
    response=answer_from_evidence('Which stand has longest life?',insights(),{})
    assert response['intent']=='COMPLETED_STAND_COMPARISON'
    assert question_scope('Why LineAlpha P7?', ['LineAlpha'])[:2]==('LineAlpha',7)


def test_ask_route_reads_actual_database_and_keeps_unknown_runtime_unknown():
    from datetime import datetime, timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    import app.models
    from app.database.session import Base
    from app.models.line import Line
    from app.models.stand_asset import StandAsset
    from app.models.stand_position import Position
    from app.models.stand_installation import StandInstallation
    from app.models.stand_event import StandCampaignEvent
    from app.api.routes.intelligence import ask_intelligence
    from app.api.routes.investigation import investigate_position
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        line=Line(name='W4');db.add(line);db.flush()
        position=Position(line_id=line.id,position_number=7);db.add(position);db.flush()
        stand=StandAsset(code='7A');db.add(stand);db.flush()
        installation=StandInstallation(stand_id=stand.id,position_id=position.id,installed_at=datetime.utcnow()-timedelta(hours=48));db.add(installation);db.flush()
        for severity,duration in [('STOPPAGE',10),('LOW',50)]:
            db.add(StandCampaignEvent(stand_id=stand.id,installation_id=installation.id,category='OBSERVATION',event_type='Inspection',severity=severity,duration_minutes=duration,recorded_by='Operator',event_at=datetime.utcnow(),created_at=datetime.utcnow()))
        db.commit()
        response=ask_intelligence(IntelligenceQuestion(question='Which stand is running for more time at W4 P7?'),db)
        assert response['provider']=='deterministic'
        assert 'W4 P7 · 7A' in response['answer']
        assert 'actual mill-running hours are unknown' in response['answer']
        investigation=investigate_position('W4',7,db)
        assert investigation['event_summary']['downtime_minutes']==10
        assert db.query(StandInstallation).count()==1
        assert not db.new and not db.dirty
    engine.dispose()


def test_plain_numeric_and_registered_custom_stand_codes_are_scoped():
    assert question_scope('Which life for stand9?', known_stands=['9'])[2]=={'9'}
    assert question_scope('How long is stand AX-22 installed?', known_stands=['AX-22'])[2]=={'AX-22'}
