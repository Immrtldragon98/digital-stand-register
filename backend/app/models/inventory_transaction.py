from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_before = Column(Integer, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    operator = Column(String(150), nullable=False)
    reason = Column(Text, nullable=False)
    transaction_type = Column(String(30), nullable=False, default="ADJUSTMENT")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    item = relationship("InventoryItem", back_populates="transactions")
