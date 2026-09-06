from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.session import Base


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("line_id", "position_number", name="uq_position_line_number"),
        CheckConstraint("position_number >= 1 AND position_number <= 10", name="ck_position_number_1_10"),
    )

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, ForeignKey("lines.id"), nullable=False)
    position_number = Column(Integer, nullable=False)
    target_life_hours = Column(Float, nullable=True)

    line = relationship("Line", back_populates="positions")
