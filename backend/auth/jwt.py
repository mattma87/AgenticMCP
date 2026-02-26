"""JWT token handling."""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import get_settings


class TokenPayload(BaseModel):
    """JWT token payload."""

    user_id: int
    role: str
    tenant_id: int
    exp: datetime


class AuthContext(BaseModel):
    """Authentication context from token."""

    user_id: int
    role: str
    tenant_id: int

    def can_access(self, resource: str, action: str) -> bool:
        """Check if user can access resource with action."""
        if self.role == "admin":
            return True
        if self.role == "reader" and action == "read":
            return True
        if self.role == "writer" and action in ("read", "write"):
            return True
        return False


class JWTManager:
    """JWT token manager."""

    def __init__(self):
        self.settings = get_settings()

    def create_token(
        self,
        user_id: int,
        role: str,
        tenant_id: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                hours=self.settings.jwt_access_token_expire_hours
            )

        payload = {
            "user_id": user_id,
            "role": role,
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            payload,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def decode_token(self, token: str) -> AuthContext:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )
            return AuthContext(
                user_id=payload["user_id"],
                role=payload["role"],
                tenant_id=payload["tenant_id"],
            )
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")


# Global instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


def create_token(user_id: int, role: str, tenant_id: int) -> str:
    """Create a JWT token."""
    return get_jwt_manager().create_token(user_id, role, tenant_id)


def decode_token(token: str) -> AuthContext:
    """Decode a JWT token."""
    return get_jwt_manager().decode_token(token)
