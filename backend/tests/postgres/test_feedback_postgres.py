from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from sqlalchemy.orm import Session
from starlette.requests import Request
from app.api.routes.feedback import FeedbackInput, submit_feedback
from app.models.feedback_report import FeedbackReport


def test_feedback_migration_and_simultaneous_retry_create_one_report(pg_engine):
    payload=FeedbackInput(request_id=uuid4(),kind='BUG',title='Concurrent retry',description='Only one report should be stored for these retries.')
    def save(_):
        with Session(pg_engine) as db:
            request=Request({'type':'http','client':('192.0.2.8',1234),'headers':[]})
            return submit_feedback(payload,request,db)
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(save,range(2)))
    assert responses[0]==responses[1]
    with Session(pg_engine) as db:
        assert db.query(FeedbackReport).count()==1
        assert db.query(FeedbackReport).one().status=='OPEN'
