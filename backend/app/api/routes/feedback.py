"""Anyone may submit feedback; report contents and triage are admin-only."""
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.config.settings import settings
from app.database.session import get_db
from app.models.feedback_report import FeedbackReport
from app.models.user import User

router = APIRouter()
Kind = Literal['BUG', 'SUGGESTION']
Status = Literal['OPEN', 'IN_PROGRESS', 'RESOLVED', 'DECLINED']


class FeedbackInput(BaseModel):
    request_id: UUID
    kind: Kind
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    page: str = Field(default='', max_length=200)
    reporter: str = Field(default='', max_length=80)

    @field_validator('title', 'description', 'reporter', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('page', mode='before')
    @classmethod
    def page_path_only(cls, value):
        if not isinstance(value, str):
            return value
        path = value.strip().split('?')[0].split('#')[0]
        if path and (not path.startswith('/') or path.startswith('//')):
            raise ValueError('Use an app page path, such as /dashboard.')
        return path


class FeedbackUpdate(BaseModel):
    status: Status
    admin_notes: str = Field(default='', max_length=2000)


def receipt(row):
    return {'id': row.id, 'reference': f'FB-{row.id:06d}', 'message': 'Report received. An admin can review it in Feedback.'}


def same_report(row, payload):
    return all(getattr(row, field) == getattr(payload, field) for field in ('kind','title','description','page','reporter'))


@router.post('/', status_code=201)
def submit_feedback(payload: FeedbackInput, request: Request, db: Session = Depends(get_db)):
    key = str(payload.request_id)
    existing = db.query(FeedbackReport).filter_by(request_id=key).first()
    if existing:
        if not same_report(existing, payload):
            raise HTTPException(409, 'This submission key belongs to a different report. Start a new report.')
        return receipt(existing)
    # Hash the peer address; do not retain raw IPs or trust caller-supplied forwarding headers.
    peer = request.client.host if request.client else 'unknown'
    client_hash = hmac.new(settings.SECRET_KEY.encode(), peer.encode(), hashlib.sha256).hexdigest()
    now = datetime.utcnow()
    recent = db.query(FeedbackReport).filter(FeedbackReport.client_hash == client_hash,
        FeedbackReport.created_at >= now-timedelta(hours=1)).count()
    if recent >= 20:
        raise HTTPException(429, 'Too many reports from this connection. Please try again later.', headers={'Retry-After':'3600'})
    row = FeedbackReport(request_id=key, kind=payload.kind, title=payload.title,
        description=payload.description, page=payload.page, reporter=payload.reporter,
        client_hash=client_hash, status='OPEN', admin_notes='', created_at=now, updated_at=now)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(FeedbackReport).filter_by(request_id=key).first()
        if existing and same_report(existing, payload):
            return receipt(existing)
        raise HTTPException(409, 'Submission conflicted. Retry the same report.')
    db.refresh(row)
    return receipt(row)


@router.get('/')
def list_feedback(status: Status | None = None, kind: Kind | None = None,
                  offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(require_admin)):
    query = db.query(FeedbackReport)
    if status:
        query = query.filter(FeedbackReport.status == status)
    if kind:
        query = query.filter(FeedbackReport.kind == kind)
    total = query.count()
    rows = query.order_by(FeedbackReport.created_at.desc(), FeedbackReport.id.desc()).offset(offset).limit(limit).all()
    fields = ('id','kind','title','description','page','reporter','status','admin_notes','updated_by','created_at','updated_at')
    return {'total': total, 'items': [{**{key:getattr(row,key) for key in fields}, 'reference':f'FB-{row.id:06d}'} for row in rows]}


@router.patch('/{report_id}')
def update_feedback(report_id: int, payload: FeedbackUpdate, db: Session = Depends(get_db),
                    user: User = Depends(require_admin)):
    row = db.query(FeedbackReport).filter_by(id=report_id).with_for_update().first()
    if row is None:
        raise HTTPException(404, 'Report not found.')
    row.status = payload.status
    row.admin_notes = payload.admin_notes.strip()
    row.updated_by = user.username
    row.updated_at = datetime.utcnow()
    db.commit()
    return {'id':row.id, 'status':row.status, 'admin_notes':row.admin_notes}
