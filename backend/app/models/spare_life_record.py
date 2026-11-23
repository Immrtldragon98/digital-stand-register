from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.database.session import Base


class SpareLifeRecord(Base):
    __tablename__ = 'spare_life_records'
    __table_args__ = (
        CheckConstraint('life_hours > 0', name='ck_spare_life_positive'),
        CheckConstraint('quantity > 0', name='ck_spare_life_quantity_positive'),
    )
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('inventory_items.id', ondelete='RESTRICT'), nullable=False, index=True)
    life_hours = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    recorded_by = Column(String(150), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
