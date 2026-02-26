"""Common models."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""

    items: List[T]
    count: int
    skip: int
    limit: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response."""

    success: bool = True
    message: str
