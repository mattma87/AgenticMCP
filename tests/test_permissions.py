"""Tests for the permissions module."""

import pytest

from agenticmcp.permissions import PermissionChecker
from agenticmcp.config import PermissionsConfig, RoleDef, TableDef, ColumnDef


@pytest.fixture
def sample_permissions() -> PermissionsConfig:
    """Create a sample permissions configuration."""
    return PermissionsConfig(
        version="1.0",
        default_role="reader",
        roles={
            "admin": RoleDef(
                description="Full access",
                tables=["*"],
                operations=["*"],
            ),
            "reader": RoleDef(
                description="Read only",
                tables=["users", "products"],
                operations=["read"],
                columns={
                    "users": ["id", "name"],  # No email
                },
            ),
            "writer": RoleDef(
                description="Read and write",
                tables=["users", "orders"],
                operations=["read", "write"],
                row_filters={
                    "orders": "user_id = {user_id}",
                },
            ),
        },
        tables={
            "users": TableDef(
                primary_key="id",
                columns=[
                    ColumnDef(name="id", type="integer"),
                    ColumnDef(name="email", type="text", sensitive=True),
                    ColumnDef(name="name", type="text"),
                ],
            ),
            "products": TableDef(
                primary_key="id",
                columns=[
                    ColumnDef(name="id", type="integer"),
                    ColumnDef(name="name", type="text"),
                ],
            ),
        },
    )


def test_admin_full_access(sample_permissions: PermissionsConfig) -> None:
    """Test admin role has full access."""
    with sample_permissions_ctx(sample_permissions, "admin"):
        checker = PermissionChecker()

        assert checker.is_admin() is True
        assert checker.can_access_table("users") is True
        assert checker.can_read("users") is True
        assert checker.can_write("users") is True
        assert checker.can_execute_raw_query() is True


def test_reader_read_only(sample_permissions: PermissionsConfig) -> None:
    """Test reader role has read-only access."""
    with sample_permissions_ctx(sample_permissions, "reader"):
        checker = PermissionChecker()

        assert checker.is_admin() is False
        assert checker.can_read("users") is True
        assert checker.can_write("users") is False
        assert checker.can_execute_raw_query() is False


def test_reader_column_filtering(sample_permissions: PermissionsConfig) -> None:
    """Test column filtering for reader role."""
    with sample_permissions_ctx(sample_permissions, "reader"):
        checker = PermissionChecker()

        allowed = checker.get_allowed_columns("users")
        assert allowed == ["id", "name"]  # No email

        rows = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        filtered = checker.filter_result_columns("users", rows)
        assert filtered == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]


def test_writer_no_access_to_unauthorized_tables(
    sample_permissions: PermissionsConfig,
) -> None:
    """Test writer cannot access tables not in their list."""
    with sample_permissions_ctx(sample_permissions, "writer"):
        checker = PermissionChecker()

        assert checker.can_access_table("users") is True
        assert checker.can_access_table("orders") is True
        assert checker.can_access_table("products") is False


def test_permission_denied_exception(sample_permissions: PermissionsConfig) -> None:
    """Test permission denied exception is raised."""
    with sample_permissions_ctx(sample_permissions, "reader"):
        checker = PermissionChecker()

        with pytest.raises(PermissionError) as exc_info:
            checker.check_permission("write", "users")

        assert "not allowed" in str(exc_info.value)
        assert "write" in str(exc_info.value)


def test_row_filter_substitution(sample_permissions: PermissionsConfig) -> None:
    """Test row-level security filter substitution."""
    with sample_permissions_ctx(sample_permissions, "writer", user_id="123"):
        checker = PermissionChecker()

        filter_sql = checker.get_row_filter("orders")
        assert filter_sql == "user_id = 123"


def test_accessible_tables(sample_permissions: PermissionsConfig) -> None:
    """Test getting accessible tables for a role."""
    with sample_permissions_ctx(sample_permissions, "reader"):
        checker = PermissionChecker()

        tables = checker.get_accessible_tables()
        assert set(tables) == {"users", "products"}


def test_row_limit_application(sample_permissions: PermissionsConfig) -> None:
    """Test row limit is applied correctly."""
    with sample_permissions_ctx(sample_permissions, "reader"):
        checker = PermissionChecker()

        # Respects lower limit
        assert checker.apply_row_limit(10) == 10

        # Respects max_rows
        assert checker.apply_row_limit(2000) == checker.max_rows

        # Uses default for None
        limit = checker.apply_row_limit(None)
        assert limit == checker.max_rows


from contextlib import contextmanager
from unittest.mock import patch, MagicMock


@contextmanager
def sample_permissions_ctx(
    permissions: PermissionsConfig,
    role: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
):
    """Context manager for testing with specific permissions."""
    with patch('agenticmcp.permissions.get_permissions') as mock_get_perm:
        mock_get_perm.return_value = permissions
        with patch('agenticmcp.permissions.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.role = role
            mock_settings.user_id = user_id
            mock_settings.tenant_id = tenant_id
            mock_settings.max_query_rows = 1000
            mock_settings.load_permissions.return_value = permissions
            mock_get_settings.return_value = mock_settings
            yield
