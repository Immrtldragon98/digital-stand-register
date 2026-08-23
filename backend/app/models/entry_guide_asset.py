from sqlalchemy import Column, Float, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import LocationEnum, StatusEnum, EntryGuideConditionEnum


class EntryGuideAsset(Base):
    __tablename__ = "entry_guide_assets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)

    current_location = Column(Enum(LocationEnum), nullable=False, default=LocationEnum.WIP)
    current_status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.YET_TO_READY)
    current_position_id = Column(Integer, ForeignKey("positions.id"), nullable=True, unique=True)

    condition = Column(Enum(EntryGuideConditionEnum), nullable=False, default=EntryGuideConditionEnum.OLD)
    lifetime_hours = Column(Float, nullable=False, default=0.0)
    condition_notes = Column(String(500), nullable=True)

    installations = relationship("EntryGuideInstallation", back_populates="guide")
