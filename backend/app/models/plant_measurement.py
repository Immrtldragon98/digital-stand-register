from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from app.database.session import Base


class PreparationCycle(Base):
    __tablename__ = 'preparation_cycles'
    __table_args__ = (Index('uq_open_preparation_cycle', 'stand_id', unique=True, postgresql_where=text('finished_at IS NULL'), sqlite_where=text('finished_at IS NULL')),)
    id = Column(Integer, primary_key=True)
    stand_id = Column(Integer, ForeignKey('stand_assets.id'), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_by = Column(String(100), nullable=False)
    finished_at = Column(DateTime)
    finished_by = Column(String(100))


class MaintenanceMeasurement(Base):
    __tablename__ = 'maintenance_measurements'
    id = Column(Integer, primary_key=True)
    request_id = Column(String(36), unique=True, nullable=False)
    kind = Column(String(24), nullable=False)
    duration_minutes = Column(Float)
    description = Column(Text, nullable=False)
    stand_id = Column(Integer, ForeignKey('stand_assets.id'))
    item_id = Column(Integer, ForeignKey('inventory_items.id'))
    recorded_by = Column(String(100), nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class ValueBaseline(Base):
    __tablename__ = 'value_baselines'
    metric = Column(String(40), primary_key=True)
    value = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    source = Column(String(500), nullable=False)
    recorded_by = Column(String(100), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class RuntimeConfirmation(Base):
    __tablename__ = 'runtime_confirmations'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id'), nullable=False, index=True)
    state = Column(String(10), nullable=False)
    confirmed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    confirmed_by = Column(String(100), nullable=False)
