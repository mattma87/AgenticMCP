"""Authentication models."""

from pydantic import BaseModel, Field
from typing import Optional


class TokenRequest(BaseModel):
    """Token request."""

    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="User role (admin, reader, writer)")
    tenant_id: int = Field(1, description="Tenant ID for multi-tenant")


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_id: int
    role: str
    tenant_id: int


class TokenInfoResponse(BaseModel):
    """Token info response."""

    user_id: int
    role: str
    tenant_id: int
    valid: bool
