from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship
from app.database.session import Base


class StandInstallation(Base):
    __tablename__ = "stand_installations"
    __table_args__ = (
        Index(
            "uq_active_stand_installation_position",
            "position_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_active_stand_installation_asset",
            "stand_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    stand_id = Column(Integer, ForeignKey("stand_assets.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)
    installed_by = Column(String(100), nullable=True)
    removed_by = Column(String(100), nullable=True)
    removal_reason = Column(String(500), nullable=True)
    campaign_hours = Column(Float, nullable=True)

    stand = relationship("StandAsset", back_populates="installations")
