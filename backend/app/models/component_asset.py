from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from app.database.session import Base


class ComponentAsset(Base):
    __tablename__ = 'component_assets'
    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    component_type_id = Column(Integer, ForeignKey('stand_component_types.id'), nullable=False, index=True)
    condition = Column(String(12), nullable=False)  # NEW or REUSED
    prior_life_hours = Column(Float, nullable=True)  # None means unknown pre-register life
    created_at = Column(DateTime, nullable=False)


class ComponentFitting(Base):
    __tablename__ = 'component_fittings'
    __table_args__ = (Index('uq_active_component_fitting', 'asset_id', unique=True,
        postgresql_where=text('removed_at IS NULL'), sqlite_where=text('removed_at IS NULL')),)
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('component_assets.id'), nullable=False, index=True)
    stand_id = Column(Integer, ForeignKey('stand_assets.id'), nullable=False, index=True)
    preparation_id = Column(Integer, ForeignKey('stand_component_preparations.id'), nullable=False)
    fitted_at = Column(DateTime, nullable=False)
    removed_at = Column(DateTime, nullable=True)


class PreparationAssetSelection(Base):
    __tablename__ = 'preparation_asset_selections'
    __table_args__ = (UniqueConstraint('preparation_id', 'asset_id', name='uq_preparation_component_asset'),)
    id = Column(Integer, primary_key=True)
    preparation_id = Column(Integer, ForeignKey('stand_component_preparations.id', ondelete='CASCADE'), nullable=False, index=True)
    component_type_id = Column(Integer, ForeignKey('stand_component_types.id'), nullable=False)
    asset_id = Column(Integer, ForeignKey('component_assets.id'), nullable=False)
