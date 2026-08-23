from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    quantity: int = Field(default=0, ge=0)
    minimum_quantity: int = Field(default=0, ge=0)
    location: str = Field(min_length=1, max_length=150)
    remarks: str | None = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    minimum_quantity: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, min_length=1, max_length=150)
    remarks: str | None = None


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
