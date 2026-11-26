from app.services.maintenance_assistant_service import enhanced_answer, resolve_scope
from test_intelligence_answers import insights


def test_followup_scope_is_explicit_and_new_line_does_not_reuse_position():
    query, scope = resolve_scope('Why did it fail?', {'line':'W1','position':7}, insights())
    assert query.endswith('at W1 P7') and scope == {'line':'W1','position':7}
    query, scope = resolve_scope('What about W4?', {'line':'W1','position':7,'topic':'COMPLETED_STAND_COMPARISON'}, insights())
    assert query.startswith('Compare completed stand life') and scope == {'line':'W4','position':None}
    assert resolve_scope('Compare all lines', {'line':'W1','position':7}, insights())[1] is None
    assert resolve_scope('Why?', {'line':'Nonexistent','position':7}, insights())[1] is None


def test_current_stock_preserves_zero_unknown_and_ignores_inactive_history():
    items = [{'name':'Bearing','quantity':None,'minimum':4}, {'name':'Seal','quantity':0,'minimum':0}]
    response = enhanced_answer('Current stock', insights(), {'top_spares':[{'spare':'Wrong historical total','quantity':999}]}, items=items)
    assert response['intent'] == 'CURRENT_STOCK'
    assert 'Unverified balance' in response['answer'] and '0 available' in response['answer']
    assert '999' not in response['answer'] and response['missing_evidence']
    filtered = enhanced_answer('Current stock bearing at W1 P7', insights(), {}, items=items)
    assert [r['label'] for r in filtered['facts']] == ['Bearing']
    natural = enhanced_answer('How many bearings do we have?', insights(), {}, items=items)
    assert natural['intent'] == 'CURRENT_STOCK' and natural['facts'][0]['label'] == 'Bearing'
    absent = enhanced_answer('Current stock gearbox', insights(), {}, items=items)
    assert not absent['facts'] and 'No matching' in absent['answer']


def test_spare_life_uses_completed_evidence_and_labels_manual_estimates():
    items = [{'name':'Bearing','quantity':99,'minimum':2,'average_life_hours':50,'average_life_source':'COMPLETED_RECORDS','life_sample_count':3}, {'name':'Seal','quantity':3,'minimum':2,'average_life_hours':12,'average_life_source':'MANUAL','life_sample_count':0}]
    response = enhanced_answer('Average spare life', insights(), {}, items=items)
    assert response['intent'] == 'SPARE_LIFE'
    assert '2d 2h' in response['answer'] and '3 completed units' in response['answer']
    assert 'manual estimate, no completed samples' in response['answer']
    assert response['missing_evidence'] and '99' not in response['answer']


def test_runtime_unknown_explains_evidence_without_inventing_start_stop():
    plant = {'lines':[{'name':'W1','state':'UNKNOWN','needs_confirmation':True}]}
    result = enhanced_answer('Why is runtime unknown?', insights(), {}, plant=plant)
    assert result['intent'] == 'RUNTIME_STATUS' and 'Runtime not recorded' in result['answer']
    assert result['links'][0]['href'] == '/runtime'
    assert 'cannot reconstruct' in result['limitations'][0]


def test_investigation_exposes_missing_evidence_without_diagnosis():
    result = enhanced_answer('Why W1 P7 weak?', insights(), {'position_investigation':{'line':'W1','position':7,'campaigns':0},'data':{'process_observations':0}}, scope={'line':'W1','position':7})
    assert len(result['missing_evidence']) == 3
    assert 'not diagnosed causes' in result['hypotheses'][0]
    assert result['scope']['topic'] == 'INVESTIGATION'
    assert result['links'][0]['href'] == '/investigation?line=W1&position=7'


def test_live_route_reads_stock_life_and_keeps_database_unchanged():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.database.session import Base
    import app.models
    from app.models.inventory_item import InventoryItem
    from app.models.spare_life_record import SpareLifeRecord
    from app.api.routes.intelligence import ask_intelligence, IntelligenceQuestion
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        item=InventoryItem(name='Bearing', quantity=0, minimum_quantity=2)
        db.add(item);db.flush()
        db.add(InventoryItem(name='Inactive bearing',quantity=100,is_active=False))
        db.add(SpareLifeRecord(item_id=item.id,life_hours=48,quantity=2,recorded_by='Tester'))
        db.commit()
        stock=ask_intelligence(IntelligenceQuestion(question='Current stock bearing'),db)
        assert '0 available' in stock['answer'] and 'Inactive' not in stock['answer']
        life=ask_intelligence(IntelligenceQuestion(question='Average bearing life'),db)
        assert '2d 0h' in life['answer'] and '2 completed units' in life['answer']
        assert db.query(SpareLifeRecord).count()==1 and not db.dirty and not db.new
    engine.dispose()


def test_staging_allows_read_only_questions_but_blocks_all_record_changes(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from app.main import app
    from app.database.session import Base, get_db
    from test_feedback import asgi
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    monkeypatch.setenv('DSR_ENVIRONMENT','staging')
    with Session(engine) as db:
        app.dependency_overrides[get_db]=lambda:db
        try:
            assert asgi('POST','/api/v1/intelligence/ask',{'question':'Current stock'})==200
            assert asgi('POST','/api/v1/plant/measurements',{})==403
            assert asgi('POST','/api/v1/intelligence/ask/anything',{})==403
            assert not db.dirty and not db.new
        finally:
            app.dependency_overrides.pop(get_db,None)
    engine.dispose()
