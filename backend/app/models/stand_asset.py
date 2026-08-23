from sqlalchemy import Boolean, Column, Float, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import LocationEnum, StatusEnum


class StandAsset(Base):
    __tablename__ = "stand_assets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)

    current_location = Column(
        Enum(LocationEnum),
        nullable=False,
        default=LocationEnum.WIP,
    )

    current_status = Column(
        Enum(StatusEnum),
        nullable=False,
        default=StatusEnum.YET_TO_READY,
    )

    current_position_id = Column(
        Integer,
        ForeignKey("positions.id"),
        nullable=True,
        unique=True,
    )

    # Cumulative life survives history cleanup/retention.
    lifetime_hours = Column(Float, nullable=False, default=0.0)
    leakage = Column(Boolean, nullable=False, default=False)
    vibration = Column(Boolean, nullable=False, default=False)
    condition_notes = Column(String(500), nullable=True)

    installations = relationship(
        "StandInstallation",
        back_populates="stand",
    )

    preparation_events = relationship(
        "StandPreparationEvent",
        back_populates="stand",
        cascade="all, delete-orphan",
    )
