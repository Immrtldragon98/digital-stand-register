from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StandSummary(BaseModel):
    code: str
    installed_at: Optional[datetime] = None

class GuideSummary(BaseModel):
    code: str
    installed_at: Optional[datetime] = None

class PositionDashboardResponse(BaseModel):
    id: int
    position_number: int
    current_stand: Optional[StandSummary] = None
    current_guide: Optional[GuideSummary] = None
    running_days: int

class LineDashboardResponse(BaseModel):
    id: int
    name: str
    positions: List[PositionDashboardResponse]