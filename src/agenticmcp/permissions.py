"""Permission control system for database access."""

from typing import Any

from .config import get_permissions, get_settings, RoleDef


class PermissionChecker:
    """Check permissions for database operations."""

    def __init__(self) -> None:
        """Initialize the permission checker."""
        self._load_config()

    def _load_config(self) -> None:
        """Load permissions configuration."""
        settings = get_settings()
        self.permissions = get_permissions()
        self.role_name = settings.role
        self.user_id = settings.user_id
        self.tenant_id = settings.tenant_id
        self.role = self.permissions.roles.get(
            self.role_name,
            self.permissions.roles.get(self.permissions.default_role, RoleDef()),
        )
        self.max_rows = settings.max_query_rows

    def reload(self) -> None:
        """Reload permissions configuration."""
        from .config import reload_permissions

        reload_permissions()
        self._load_config()

    def is_admin(self) -> bool:
        """Check if current role has admin privileges."""
        return self.role_name == "admin" or "*" in self.role.tables

    def can_access_table(self, table_name: str) -> bool:
        """Check if current role can access a table."""
        if self.is_admin():
            return True

        # Check if table is explicitly allowed
        if table_name in self.role.tables:
            return True

        # Check for wildcard
        if "*" in self.role.tables:
            return True

        return False

    def can_read(self, table_name: str) -> bool:
        """Check if current role can read from a table."""
        if self.is_admin():
            return True

        if not self.can_access_table(table_name):
            return False

        operations = self.role.operations
        return "*" in operations or "read" in operations

    def can_write(self, table_name: str) -> bool:
        """Check if current role can write to a table."""
        if self.is_admin():
            return True

        if not self.can_access_table(table_name):
            return False

        operations = self.role.operations
        return "*" in operations or "write" in operations

    def can_execute_raw_query(self) -> bool:
        """Check if current role can execute raw SQL queries."""
        return self.is_admin()

    def get_allowed_columns(self, table_name: str) -> list[str] | None:
        """
        Get allowed columns for a table.

        Returns:
            List of column names, or None for all columns (admin)
        """
        if self.is_admin():
            return None

        # Check role-specific column restrictions
        if table_name in self.role.columns:
            return self.role.columns[table_name]

        # Check table definition for column visibility
        if table_name in self.permissions.tables:
            table_def = self.permissions.tables[table_name]
            allowed = []
            for col in table_def.columns:
                if col.visible_to is None or "*" in col.visible_to:
                    allowed.append(col.name)
                elif self.role_name in col.visible_to:
                    allowed.append(col.name)
            return allowed if allowed else None

        return None

    def get_row_filter(self, table_name: str) -> str | None:
        """
        Get row-level filter for a table.

        Returns:
            SQL WHERE clause fragment, or None
        """
        if self.is_admin():
            return None

        # Check role-specific row filters
        if table_name in self.role.row_filters:
            filter_template = self.role.row_filters[table_name]
            return self._substitute_filter_vars(filter_template)

        # Check table definition for row filters
        if table_name in self.permissions.tables:
            table_def = self.permissions.tables[table_name]
            if table_def.row_filter and self.role_name in table_def.row_filter:
                filter_template = table_def.row_filter[self.role_name]
                return self._substitute_filter_vars(filter_template)

        return None

    def _substitute_filter_vars(self, filter_template: str) -> str:
        """Substitute variables in row filter template."""
        result = filter_template

        if self.user_id is not None:
            result = result.replace("{user_id}", str(self.user_id))

        if self.tenant_id is not None:
            result = result.replace("{tenant_id}", str(self.tenant_id))

        return result

    def filter_result_columns(
        self,
        table_name: str,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter columns in result rows based on permissions."""
        allowed_columns = self.get_allowed_columns(table_name)

        if allowed_columns is None:
            # Admin - return all columns
            return rows

        filtered = []
        for row in rows:
            filtered_row = {
                k: v for k, v in row.items() if k in allowed_columns
            }
            filtered.append(filtered_row)

        return filtered

    def apply_row_limit(self, limit: int | None) -> int:
        """Apply permission-based row limit."""
        if limit is None:
            return self.max_rows

        effective_limit = min(limit, self.max_rows)
        if effective_limit <= 0:
            return self.max_rows

        return effective_limit

    def validate_operation(self, operation: str, table_name: str) -> bool:
        """Validate if an operation is permitted."""
        if operation == "read":
            return self.can_read(table_name)
        elif operation in ("insert", "update", "delete"):
            return self.can_write(table_name)
        elif operation == "query":
            return self.can_execute_raw_query()

        return False

    def get_accessible_tables(self) -> list[str]:
        """Get list of tables accessible to current role."""
        all_tables = list(self.permissions.tables.keys())

        if self.is_admin():
            return all_tables

        # Return explicitly allowed tables
        return [t for t in all_tables if self.can_access_table(t)]

    def check_permission(self, operation: str, table_name: str) -> None:
        """
        Check permission and raise exception if not allowed.

        Raises:
            PermissionError: If operation is not permitted
        """
        if not self.validate_operation(operation, table_name):
            raise PermissionError(
                f"Role '{self.role_name}' is not allowed to perform "
                f"'{operation}' on table '{table_name}'"
            )

    def get_permission_summary(self) -> dict[str, Any]:
        """Get summary of current role's permissions."""
        return {
            "role": self.role_name,
            "description": self.role.description,
            "tables": self.role.tables,
            "operations": self.role.operations,
            "column_restrictions": self.role.columns,
            "row_filters": self.role.row_filters,
            "accessible_tables": self.get_accessible_tables(),
            "can_execute_raw_query": self.can_execute_raw_query(),
        }


# Global permission checker instance
_permission_checker: PermissionChecker | None = None


def get_permissions_checker() -> PermissionChecker:
    """Get global permission checker instance."""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker


def reload_permissions_checker() -> None:
    """Reload permissions configuration."""
    global _permission_checker
    if _permission_checker is not None:
        _permission_checker.reload()
    else:
        _permission_checker = PermissionChecker()
