from datetime import datetime

from pydantic import BaseModel, Field
from app.models.enums import StatusEnum


class InstallStandSchema(BaseModel):
    stand_code: str
    position_id: int
    operator_name: str | None = None


class RemoveStandSchema(BaseModel):
    stand_code: str
    operator_name: str | None = None
    reason: str | None = None


class MarkReadySchema(BaseModel):
    stand_code: str


class UpdatePreparationStatusSchema(BaseModel):
    stand_code: str
    status: StatusEnum
    updated_by: str = Field(min_length=1, max_length=100)
    remarks: str | None = Field(default=None, max_length=500)


class ChangeStandSchema(BaseModel):
    position_id: int
    removed_stand_code: str
    installed_stand_code: str
    changed_by: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=255)
    changed_at: datetime | None = None
    notes: str | None = None
    removed_condition: str | None = None
    leakage: bool = False
    vibration: bool = False
