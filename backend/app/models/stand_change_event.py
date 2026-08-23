from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.database.session import Base


class StandChangeEvent(Base):
    __tablename__ = "stand_change_events"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    removed_stand_id = Column(Integer, ForeignKey("stand_assets.id"), nullable=False)
    installed_stand_id = Column(Integer, ForeignKey("stand_assets.id"), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    changed_by = Column(String(100), nullable=False)
    reason = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    removed_condition = Column(String(100), nullable=True)
