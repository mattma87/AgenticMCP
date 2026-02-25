"""Configuration management for AgenticMCP server."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ColumnDef(BaseModel):
    """Column definition."""

    name: str
    type: str
    sensitive: bool = False
    visible_to: list[str] | None = None


class TableDef(BaseModel):
    """Table definition."""

    primary_key: str = "id"
    columns: list[ColumnDef] = []
    row_filter: dict[str, str] | None = None


class RoleDef(BaseModel):
    """Role definition."""

    description: str = ""
    tables: list[str] = []
    operations: list[str] = []
    columns: dict[str, list[str]] = {}
    row_filters: dict[str, str] = {}


class PermissionsConfig(BaseModel):
    """Permissions configuration."""

    version: str = "1.0"
    default_role: str = "reader"
    roles: dict[str, RoleDef] = {}
    tables: dict[str, TableDef] = {}

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: dict[str, RoleDef]) -> dict[str, RoleDef]:
        """Validate roles configuration."""
        if "admin" not in v:
            # Add default admin role
            v["admin"] = RoleDef(
                description="Full access to all tables",
                tables=["*"],
                operations=["*"],
            )
        return v


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = ""
    db_pool_size: int = 10
    db_pool_min_size: int = 2

    # Permission settings
    role: str = "reader"
    user_id: str | None = None
    tenant_id: str | None = None
    permissions_file: str = "config/permissions.yaml"

    # Query settings
    max_query_rows: int = 1000
    query_timeout: int = 30

    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def load_permissions(self) -> PermissionsConfig:
        """Load permissions configuration from file."""
        permissions_path = Path(self.permissions_file)
        if not permissions_path.exists():
            # Try relative to project root
            project_root = Path(__file__).parent.parent.parent
            permissions_path = project_root / self.permissions_file

        if permissions_path.exists():
            with open(permissions_path) as f:
                data = yaml.safe_load(f) or {}
            return PermissionsConfig(**data)
        else:
            # Return default permissions
            return PermissionsConfig()


# Global settings instance
_settings: Settings | None = None
_permissions: PermissionsConfig | None = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_permissions() -> PermissionsConfig:
    """Get global permissions configuration."""
    global _permissions
    if _permissions is None:
        _permissions = get_settings().load_permissions()
    return _permissions


def reload_permissions() -> PermissionsConfig:
    """Reload permissions configuration."""
    global _permissions
    _permissions = get_settings().load_permissions()
    return _permissions
