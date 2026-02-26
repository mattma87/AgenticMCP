"""FastAPI dependencies."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth.jwt import decode_token, AuthContext
from backend.config import get_settings

security = HTTPBearer()


async def get_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """Extract token from Authorization header."""
    return credentials.credentials


async def get_auth_context(
    token: Annotated[str, Depends(get_token)]
) -> AuthContext:
    """Get authentication context from JWT token."""
    try:
        return decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_auth_context(
    token: Annotated[Optional[str], Depends(get_token)] = None
) -> Optional[AuthContext]:
    """Optional authentication - returns None if no token provided."""
    if token is None:
        return None
    try:
        return decode_token(token)
    except ValueError:
        return None


# Type aliases for commonly used dependencies
AuthDep = Annotated[AuthContext, Depends(get_auth_context)]
OptionalAuthDep = Annotated[Optional[AuthContext], Depends(optional_auth_context)]
