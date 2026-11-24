from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, CheckConstraint, UniqueConstraint
from app.database.session import Base

class LineRuntimeEvent(Base):
    __tablename__ = 'line_runtime_events'
    __table_args__ = (CheckConstraint("state IN ('RUNNING','STOPPED')", name='ck_line_runtime_state'), UniqueConstraint('line_id','event_at',name='uq_line_runtime_at'))
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id', ondelete='RESTRICT'), nullable=False, index=True)
    state = Column(String(10), nullable=False)
    event_at = Column(DateTime, nullable=False, index=True)
    recorded_by = Column(String(100), nullable=False)
    reason = Column(String(500), nullable=True)
