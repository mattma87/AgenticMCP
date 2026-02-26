"""Backend configuration."""

import os
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend application settings."""

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AgenticMCP Backend"
    app_version: str = "1.0.0"
    debug: bool = Field(default=True)  # Default to True for easier testing

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "agenticmcp"
    db_user: str = "postgres"
    db_password: str = ""
    db_pool_size: int = 10

    # JWT
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24

    # Admin user (created on startup if not exists)
    admin_user_id: int = 1
    admin_role: str = "admin"
    admin_tenant_id: int = 1

    @property
    def database_url(self) -> str:
        """Build database URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key."""
        # First try BACKEND_JWT_SECRET, then JWT_SECRET, then default
        key = os.getenv("BACKEND_JWT_SECRET") or os.getenv("JWT_SECRET") or self.jwt_secret_key
        # In debug mode, allow default secret
        if self.debug:
            return key or self.jwt_secret_key
        if key == "change-this-secret-key-in-production":
            raise ValueError("JWT_SECRET must be set in production")
        return key


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
