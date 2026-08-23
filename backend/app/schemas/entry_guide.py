from pydantic import BaseModel, Field
from app.models.enums import EntryGuideConditionEnum


class InstallEntryGuideSchema(BaseModel):
    guide_code: str
    position_id: int
    operator_name: str | None = None


class RemoveEntryGuideSchema(BaseModel):
    guide_code: str
    removed_by: str = Field(min_length=1, max_length=100)
    removal_reason: str = Field(min_length=1, max_length=500)


class UpdateEntryGuideConditionSchema(BaseModel):
    guide_code: str
    condition: EntryGuideConditionEnum
    notes: str | None = None
