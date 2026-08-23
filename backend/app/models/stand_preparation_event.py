from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import StatusEnum


class StandPreparationEvent(Base):
    __tablename__ = "stand_preparation_events"

    id = Column(Integer, primary_key=True, index=True)
    stand_id = Column(Integer, ForeignKey("stand_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(Enum(StatusEnum), nullable=False)
    to_status = Column(Enum(StatusEnum), nullable=False)
    updated_by = Column(String(100), nullable=False)
    remarks = Column(String(500), nullable=True)
    changed_at = Column(DateTime, nullable=False)

    stand = relationship("StandAsset", back_populates="preparation_events")
