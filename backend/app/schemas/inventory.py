from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    quantity: int = Field(default=0, ge=0)
    minimum_quantity: int = Field(default=0, ge=0)
    location: str = Field(default="Store", min_length=1, max_length=150)
    remarks: str | None = None
    expected_life_hours: float | None = Field(default=None, ge=0)
    observed_avg_life_hours: float | None = Field(default=None, ge=0)
    reliability_pct: float | None = Field(default=None, ge=0, le=100)
    availability_pct: float | None = Field(default=None, ge=0, le=100)
    criticality: str = Field(default="MEDIUM", min_length=1, max_length=20)
    used_at: str | None = Field(default=None, max_length=150)


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    minimum_quantity: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, min_length=1, max_length=150)
    remarks: str | None = None
    expected_life_hours: float | None = Field(default=None, ge=0)
    observed_avg_life_hours: float | None = Field(default=None, ge=0)
    reliability_pct: float | None = Field(default=None, ge=0, le=100)
    availability_pct: float | None = Field(default=None, ge=0, le=100)
    criticality: str | None = Field(default=None, min_length=1, max_length=20)
    used_at: str | None = Field(default=None, max_length=150)


class InventoryQuantityChange(BaseModel):
    delta: int
    operator: str = Field(min_length=1, max_length=150)
    reason: str = Field(min_length=1, max_length=1000)


class InventorySetQuantity(BaseModel):
    quantity: int = Field(ge=0)
    operator: str = Field(min_length=1, max_length=150)
    reason: str = Field(min_length=1, max_length=1000)


class InventoryOut(InventoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InventoryTransactionOut(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity_before: int
    quantity_change: int
    quantity_after: int
    operator: str
    reason: str
    transaction_type: str
    created_at: datetime
