from sqlalchemy import Boolean, Column, Date, Float, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.database.session import Base


class HistoricalCampaign(Base):
    __tablename__ = "historical_campaigns"
    __table_args__ = (
        UniqueConstraint("source_file", "line_name", "position_number", "stand_code", "installed_date", name="uq_historical_campaign"),
    )

    id = Column(Integer, primary_key=True, index=True)
    line_name = Column(String(10), nullable=False, index=True)
    position_number = Column(Integer, nullable=False, index=True)
    stand_code = Column(String(50), nullable=False, index=True)
    installed_date = Column(Date, nullable=False)
    removed_date = Column(Date, nullable=True)
    life_days = Column(Float, nullable=True)
    removal_reason = Column(Text, nullable=True)
    inferred = Column(Boolean, nullable=False, default=True)
    confidence = Column(Float, nullable=False, default=0.75)
    source_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HistoricalSpareUsage(Base):
    __tablename__ = "historical_spare_usage"
    __table_args__ = (
        UniqueConstraint("source_file", "usage_date", "spare_name", name="uq_historical_spare_usage"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    spare_name = Column(String(150), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    source_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProcessObservation(Base):
    __tablename__ = "process_observations"
    __table_args__ = (
        UniqueConstraint("source_file", "line_name", "observation_date", "shift", "coil_no", name="uq_process_observation"),
    )

    id = Column(Integer, primary_key=True, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    shift = Column(String(20), nullable=True)
    source_wrm = Column(Integer, nullable=False)
    line_name = Column(String(10), nullable=False, index=True)
    coil_no = Column(String(80), nullable=True, index=True)
    uts_band = Column(String(30), nullable=True)
    casting_speed = Column(Float, nullable=True)
    emulsion_temp = Column(Float, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    source_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
