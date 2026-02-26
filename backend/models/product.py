"""Product models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    stock: int = Field(0, ge=0)


class ProductCreate(ProductBase):
    """Product creation model."""

    tenant_id: int = 1


class ProductUpdate(BaseModel):
    """Product update model."""

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None


class ProductResponse(ProductBase):
    """Product response model."""

    id: int
    tenant_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response."""

    products: List[ProductResponse]
    count: int
