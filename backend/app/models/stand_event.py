from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class StandCampaignEvent(Base):
    __tablename__ = "stand_campaign_events"

    id = Column(Integer, primary_key=True, index=True)
    stand_id = Column(Integer, ForeignKey("stand_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    installation_id = Column(Integer, ForeignKey("stand_installations.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(24), nullable=False, default="OBSERVATION")
    event_type = Column(String(100), nullable=False)
    severity = Column(String(16), nullable=False, default="LOW")
    component_name = Column(String(100), nullable=True)
    duration_minutes = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    event_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    recorded_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    stand = relationship("StandAsset")
    installation = relationship("StandInstallation")
