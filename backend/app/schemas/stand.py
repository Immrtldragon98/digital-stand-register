from pydantic import BaseModel
from typing import Optional
from app.models.stand_asset import LocationEnum, StatusEnum

class StandAssetResponse(BaseModel):
    id: int
    code: str
    current_location: LocationEnum
    current_status: StatusEnum
    current_position_id: Optional[int] = None

    class Config:
        from_attributes = True