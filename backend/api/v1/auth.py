"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from backend.auth.jwt import create_token, get_jwt_manager, decode_token, AuthContext
from backend.config import get_settings
from backend.models.auth import TokenRequest, TokenResponse, TokenInfoResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse)
async def create_access_token(request: TokenRequest):
    """
    Create a JWT access token.

    This endpoint generates a JWT token for the given user.
    In production, you would validate the user's credentials first.
    """
    settings = get_settings()
    jwt_manager = get_jwt_manager()

    # Create token
    access_token = jwt_manager.create_token(
        user_id=request.user_id,
        role=request.role,
        tenant_id=request.tenant_id,
        expires_delta=timedelta(hours=settings.jwt_access_token_expire_hours),
    )

    # Calculate expiration
    expires_in = settings.jwt_access_token_expire_hours * 3600

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=request.user_id,
        role=request.role,
        tenant_id=request.tenant_id,
    )


@router.get("/token/info", response_model=TokenInfoResponse)
async def get_token_info(
    token: str = None,
    auth: AuthContext = None,
):
    """
    Get information about the current token.

    Provide token via query parameter or Authorization header.
    """
    if auth is None and token:
        try:
            auth = decode_token(token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    if auth is None:
        raise HTTPException(status_code=401, detail="No valid token provided")

    return TokenInfoResponse(
        user_id=auth.user_id,
        role=auth.role,
        tenant_id=auth.tenant_id,
        valid=True,
    )


@router.post("/token/validate", response_model=TokenInfoResponse)
async def validate_token(auth: AuthContext):
    """Validate a JWT token."""
    return TokenInfoResponse(
        user_id=auth.user_id,
        role=auth.role,
        tenant_id=auth.tenant_id,
        valid=True,
    )
