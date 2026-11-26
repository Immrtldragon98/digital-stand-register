from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, CheckConstraint, Index
from app.database.session import Base


class FeedbackReport(Base):
    __tablename__ = 'feedback_reports'
    __table_args__ = (
        CheckConstraint("kind IN ('BUG','SUGGESTION')", name='ck_feedback_kind'),
        CheckConstraint("status IN ('OPEN','IN_PROGRESS','RESOLVED','DECLINED')", name='ck_feedback_status'),
        Index('ix_feedback_client_created', 'client_hash', 'created_at'),
    )
    id = Column(Integer, primary_key=True)
    request_id = Column(String(36), nullable=False, unique=True)
    kind = Column(String(16), nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    page = Column(String(200), nullable=False, default='')
    reporter = Column(String(80), nullable=False, default='')
    client_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default='OPEN', index=True)
    admin_notes = Column(Text, nullable=False, default='')
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
