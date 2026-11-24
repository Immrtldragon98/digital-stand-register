from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.sql import func
from app.database.session import Base
class CommandReceipt(Base):
    __tablename__ = 'command_receipts'
    __table_args__ = (UniqueConstraint('user_id', 'request_key', name='uq_command_user_key'),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    request_key = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    scope = Column(String(100), nullable=False)
    response = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
