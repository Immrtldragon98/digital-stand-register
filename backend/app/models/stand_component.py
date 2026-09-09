from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class StandComponentType(Base):
    __tablename__ = "stand_component_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    required_qty = Column(Integer, nullable=True)
    even_position_extra = Column(Boolean, nullable=False, default=False)
    expected_life_hours = Column(Float, nullable=True)
    criticality = Column(String(16), nullable=True)
    active = Column(Boolean, nullable=False, default=True)


class StandComponentPreparation(Base):
    __tablename__ = "stand_component_preparations"

    id = Column(Integer, primary_key=True, index=True)
    stand_id = Column(Integer, ForeignKey("stand_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    state = Column(String(20), nullable=False, default="SAVED")  # SAVED, SKIPPED, FINALIZED
    prepared_by = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    finalized_at = Column(DateTime, nullable=True)

    stand = relationship("StandAsset")
    items = relationship("StandComponentPreparationItem", back_populates="preparation", cascade="all, delete-orphan")


class StandComponentPreparationItem(Base):
    __tablename__ = "stand_component_preparation_items"

    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("stand_component_preparations.id", ondelete="CASCADE"), nullable=False, index=True)
    component_type_id = Column(Integer, ForeignKey("stand_component_types.id"), nullable=False, index=True)
    new_qty = Column(Integer, nullable=False, default=0)
    reused_qty = Column(Integer, nullable=False, default=0)
    carried_life_hours = Column(Float, nullable=True)

    preparation = relationship("StandComponentPreparation", back_populates="items")
    component_type = relationship("StandComponentType")
