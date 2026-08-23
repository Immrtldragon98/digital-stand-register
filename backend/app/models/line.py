from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.session import Base
class Line(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    positions = relationship("Position", back_populates="line")