"""User models."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user model."""

    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """User creation model."""

    password: Optional[str] = Field(None, min_length=8)
    tenant_id: int = 1


class UserUpdate(BaseModel):
    """User update model."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """User response model."""

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Email is masked by default
    email: Optional[str] = Field(None, description="Email (masked based on role)")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response."""

    users: List[UserResponse]
    count: int
