"""Order models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class OrderItemBase(BaseModel):
    """Base order item model."""

    product_id: int
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)


class OrderBase(BaseModel):
    """Base order model."""

    user_id: int
    status: str = "pending"


class OrderCreate(OrderBase):
    """Order creation model."""

    items: List[OrderItemBase] = []
    tenant_id: int = 1


class OrderResponse(OrderBase):
    """Order response model."""

    id: int
    total: Decimal
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response."""

    orders: List[OrderResponse]
    count: int
