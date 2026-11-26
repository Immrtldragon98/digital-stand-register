import asyncio
import json
from uuid import uuid4
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
import app.models
from app.main import app
from app.database.session import Base, get_db
from app.models.feedback_report import FeedbackReport
from app.models.user import User
from app.auth.jwt import create_access_token
from app.api.routes.feedback import FeedbackInput, FeedbackUpdate, submit_feedback, list_feedback, update_feedback


@pytest.fixture
def db():
    engine=create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([User(username='feedback-admin',role_id=1,hashed_password='test-only'),User(username='feedback-operator',role_id=2,hashed_password='test-only')])
        session.commit()
        yield session
    engine.dispose()


def payload(**changes):
    return FeedbackInput(**{**dict(request_id=uuid4(),kind='BUG',title='Cannot refresh stands',description='Refresh does not update the running stand list.',page='/dashboard?token=must-not-be-stored',reporter=' Shift engineer '),**changes})


def request(peer='192.0.2.1'):
    return Request({'type':'http','client':(peer,1234),'headers':[]})


def test_retries_get_same_receipt_without_duplicate_or_private_fields(db):
    p=payload();result=submit_feedback(p,request(),db)
    assert result['reference']=='FB-000001'
    assert submit_feedback(p,request(),db)==result
    assert db.query(FeedbackReport).count()==1
    row=db.query(FeedbackReport).one()
    assert row.page=='/dashboard' and row.reporter=='Shift engineer'
    assert row.status=='OPEN' and len(row.client_hash)==64
    assert set(result)=={'id','reference','message'}
    with pytest.raises(HTTPException) as error:
        submit_feedback(payload(request_id=p.request_id,title='Different report'),request(),db)
    assert error.value.status_code==409


@pytest.mark.parametrize('changes',[{'title':'  '},{'description':'too short'},{'kind':'OTHER'},{'request_id':'bad-id'},{'page':'https://example.com/'},{'description':'x'*5001}])
def test_invalid_or_unbounded_report_is_rejected(changes):
    with pytest.raises(ValidationError):payload(**changes)


def test_rate_limit_does_not_block_receipt_recovery(db):
    first=payload()
    submit_feedback(first,request(),db)
    for _ in range(19):submit_feedback(payload(kind='SUGGESTION'),request(),db)
    with pytest.raises(HTTPException) as error:submit_feedback(payload(),request(),db)
    assert error.value.status_code==429
    assert submit_feedback(first,request(),db)['id']==1


def test_admin_filters_and_status_notes_are_persisted(db):
    result=submit_feedback(payload(kind='SUGGESTION'),request(),db)
    admin=db.query(User).filter_by(role_id=1).one()
    update_feedback(result['id'],FeedbackUpdate(status='IN_PROGRESS',admin_notes='Review with mill users'),db,admin)
    data=list_feedback(status='IN_PROGRESS',kind='SUGGESTION',offset=0,limit=25,db=db,user=admin)
    assert data['total']==1 and data['items'][0]['admin_notes']=='Review with mill users'
    assert data['items'][0]['updated_by']=='feedback-admin'
    assert 'client_hash' not in data['items'][0] and 'request_id' not in data['items'][0]
    with pytest.raises(ValidationError):FeedbackUpdate(status='INVALID')


def asgi(method,path,body=None,token=None):
    async def call():
        messages=[];sent=False;done=asyncio.Event()
        async def receive():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':json.dumps(body).encode() if body else b'','more_body':False}
            await done.wait()
            return {'type':'http.disconnect'}
        async def send(message):
            messages.append(message)
            if message['type']=='http.response.body' and not message.get('more_body',False):done.set()
        headers=[(b'content-type',b'application/json')]
        if token:headers.append((b'authorization',f'Bearer {token}'.encode()))
        scope={'type':'http','asgi':{'version':'3.0'},'method':method,'scheme':'http','path':path,'raw_path':path.encode(),'query_string':b'','headers':headers,'client':('192.0.2.4',1234),'server':('testserver',80),'http_version':'1.1','root_path':''}
        await app(scope,receive,send)
        return next(m['status'] for m in messages if m['type']=='http.response.start')
    return asyncio.run(call())


def test_public_can_submit_but_only_admin_can_read_or_triage(db):
    app.dependency_overrides[get_db]=lambda:db
    try:
        data=payload().model_dump(mode='json')
        assert asgi('POST','/api/v1/feedback/',data)==201
        assert asgi('GET','/api/v1/feedback/')==401
        operator=create_access_token({'sub':'feedback-operator'})
        assert asgi('GET','/api/v1/feedback/',token=operator)==403
        assert asgi('PATCH','/api/v1/feedback/1',{'status':'RESOLVED'},operator)==403
        admin=create_access_token({'sub':'feedback-admin'})
        assert asgi('GET','/api/v1/feedback/',token=admin)==200
        assert asgi('PATCH','/api/v1/feedback/1',{'status':'RESOLVED','admin_notes':'Verified'},admin)==200
        assert db.get(FeedbackReport,1).status=='RESOLVED'
    finally:app.dependency_overrides.clear()
