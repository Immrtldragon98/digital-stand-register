from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship
from app.database.session import Base


class EntryGuideInstallation(Base):
    __tablename__ = "entry_guide_installations"
    __table_args__ = (
        Index(
            "uq_active_entry_guide_position",
            "position_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_active_entry_guide_asset",
            "guide_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("entry_guide_assets.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)
    installed_by = Column(String(100), nullable=True)
    removed_by = Column(String(100), nullable=True)
    removal_reason = Column(String(500), nullable=True)
    campaign_hours = Column(Float, nullable=True)

    guide = relationship("EntryGuideAsset", back_populates="installations")
