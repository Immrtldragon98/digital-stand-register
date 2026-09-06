from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    # Name is now the human-readable spare name only. Material/SAP codes are no longer used.
    name = Column(String(150), unique=True, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    minimum_quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(150), nullable=False, default="Store")
    remarks = Column(Text, nullable=True)

    # Spare-life / reliability fields. These are deliberately nullable until real plant data exists.
    expected_life_hours = Column(Float, nullable=True)
    observed_avg_life_hours = Column(Float, nullable=True)
    reliability_pct = Column(Float, nullable=True)
    availability_pct = Column(Float, nullable=True)
    criticality = Column(String(20), nullable=False, default="MEDIUM")
    used_at = Column(String(150), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    transactions = relationship("InventoryTransaction", back_populates="item", order_by="desc(InventoryTransaction.created_at)")
