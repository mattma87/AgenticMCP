"""Table operation tools (read, insert, update, delete)."""

import json
from typing import Any

from ..database import get_db
from ..permissions import get_permissions_checker


class TablesTool:
    """Table operation tools with permission checking."""

    def __init__(self) -> None:
        """Initialize the tables tool."""
        self.db = get_db()
        self.perm_checker = get_permissions_checker()

    async def list_tables(self) -> dict[str, Any]:
        """List all accessible tables."""
        all_tables = await self.db.list_tables()
        accessible = [t for t in all_tables if self.perm_checker.can_access_table(t)]

        return {
            "success": True,
            "count": len(accessible),
            "tables": accessible,
        }

    async def describe_table(self, table_name: str) -> dict[str, Any]:
        """Describe a table's schema."""
        # Check permission
        self.perm_checker.check_permission("read", table_name)

        if not await self.db.table_exists(table_name):
            return {
                "success": False,
                "error": f"Table '{table_name}' does not exist",
            }

        columns = await self.db.describe_table(table_name)
        allowed_columns = self.perm_checker.get_allowed_columns(table_name)

        # Filter columns if needed
        if allowed_columns is not None:
            columns = [
                c for c in columns if c["column_name"] in allowed_columns
            ]

        return {
            "success": True,
            "table": table_name,
            "columns": columns,
        }

    async def select(
        self,
        table: str,
        columns: list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Select rows from a table."""
        # Check permission
        self.perm_checker.check_permission("read", table)

        # Validate table exists
        if not await self.db.table_exists(table):
            return {
                "success": False,
                "error": f"Table '{table}' does not exist",
            }

        # Build query
        query, params = self.db.build_select_query(
            table, columns, where, order_by, limit, offset
        )

        # Apply row filter if configured
        row_filter = self.perm_checker.get_row_filter(table)
        if row_filter:
            if where:
                query = query.replace(" WHERE ", f" WHERE {row_filter} AND ")
            else:
                query = query.replace(" FROM ", f" FROM {table} WHERE {row_filter} ")

        # Apply row limit
        effective_limit = self.perm_checker.apply_row_limit(limit)
        if effective_limit != limit:
            # Update limit in query
            if limit is None:
                query += f" LIMIT {effective_limit}"
            else:
                # Replace existing limit
                query = query.rsplit(" LIMIT ", 1)[0] + f" LIMIT {effective_limit}"

        try:
            results = await self.db.execute_query(query, params)

            # Filter columns based on permissions
            filtered_results = self.perm_checker.filter_result_columns(table, results)

            return {
                "success": True,
                "count": len(filtered_results),
                "data": self._format_results(filtered_results),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def insert(
        self,
        table: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Insert a row into a table."""
        # Check permission
        self.perm_checker.check_permission("insert", table)

        # Validate table exists
        if not await self.db.table_exists(table):
            return {
                "success": False,
                "error": f"Table '{table}' does not exist",
            }

        # Get primary key for returning
        table_def = self.perm_checker.permissions.tables.get(table)
        returning = table_def.primary_key if table_def else "id"

        # Build and execute query
        query, params = self.db.build_insert_query(table, data, returning)

        try:
            result = await self.db.execute_query(query, params, fetch="one")

            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def update(
        self,
        table: str,
        data: dict[str, Any],
        where: dict[str, Any],
    ) -> dict[str, Any]:
        """Update rows in a table."""
        # Check permission
        self.perm_checker.check_permission("update", table)

        # Validate table exists
        if not await self.db.table_exists(table):
            return {
                "success": False,
                "error": f"Table '{table}' does not exist",
            }

        # Apply row filter to where clause if configured
        row_filter = self.perm_checker.get_row_filter(table)
        if row_filter:
            # Parse row filter to extract column and value
            # This is a simplified version - production would need proper parsing
            filter_parts = row_filter.split(" = ")
            if len(filter_parts) == 2:
                filter_col = filter_parts[0].strip().strip('"')
                filter_val = filter_parts[1].strip().strip("'")
                where[filter_col] = filter_val

        # Get primary key for returning
        table_def = self.perm_checker.permissions.tables.get(table)
        returning = table_def.primary_key if table_def else "id"

        # Build and execute query
        query, params = self.db.build_update_query(table, data, where, returning)

        try:
            result = await self.db.execute_query(query, params, fetch="one")

            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def delete(
        self,
        table: str,
        where: dict[str, Any],
    ) -> dict[str, Any]:
        """Delete rows from a table."""
        # Check permission
        self.perm_checker.check_permission("delete", table)

        # Validate table exists
        if not await self.db.table_exists(table):
            return {
                "success": False,
                "error": f"Table '{table}' does not exist",
            }

        # Apply row filter to where clause if configured
        row_filter = self.perm_checker.get_row_filter(table)
        if row_filter:
            # Parse row filter to extract column and value
            filter_parts = row_filter.split(" = ")
            if len(filter_parts) == 2:
                filter_col = filter_parts[0].strip().strip('"')
                filter_val = filter_parts[1].strip().strip("'")
                where[filter_col] = filter_val

        # Get primary key for returning
        table_def = self.perm_checker.permissions.tables.get(table)
        returning = table_def.primary_key if table_def else "id"

        # Build and execute query
        query, params = self.db.build_delete_query(table, where, returning)

        try:
            result = await self.db.execute_query(query, params, fetch="one")

            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _format_results(self, results: Any) -> Any:
        """Format results for JSON serialization."""
        if isinstance(results, list):
            return [
                {
                    k: self._format_value(v)
                    for k, v in row.items()
                }
                for row in results
            ]
        return results

    def _format_value(self, value: Any) -> Any:
        """Format a single value for JSON."""
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


# Tool definitions for MCP
list_tables_tool_definition = {
    "name": "list_tables",
    "description": "List all tables accessible to the current role",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}

describe_table_tool_definition = {
    "name": "describe_table",
    "description": "Get the schema of a table",
    "inputSchema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name",
            },
        },
        "required": ["table"],
    },
}

select_tool_definition = {
    "name": "select",
    "description": "Select rows from a table. Supports filtering, sorting, and pagination.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name",
            },
            "columns": {
                "type": "array",
                "description": "Column names to select (default: all)",
                "items": {"type": "string"},
            },
            "where": {
                "type": "object",
                "description": "WHERE conditions as column-value pairs",
            },
            "order_by": {
                "type": "string",
                "description": "Column to order by",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of rows to return",
            },
            "offset": {
                "type": "integer",
                "description": "Number of rows to skip",
                "default": 0,
            },
        },
        "required": ["table"],
    },
}

insert_tool_definition = {
    "name": "insert",
    "description": "Insert a new row into a table",
    "inputSchema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name",
            },
            "data": {
                "type": "object",
                "description": "Column-value pairs to insert",
            },
        },
        "required": ["table", "data"],
    },
}

update_tool_definition = {
    "name": "update",
    "description": "Update rows in a table",
    "inputSchema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name",
            },
            "data": {
                "type": "object",
                "description": "Column-value pairs to update",
            },
            "where": {
                "type": "object",
                "description": "WHERE conditions to identify rows",
            },
        },
        "required": ["table", "data", "where"],
    },
}

delete_tool_definition = {
    "name": "delete",
    "description": "Delete rows from a table",
    "inputSchema": {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name",
            },
            "where": {
                "type": "object",
                "description": "WHERE conditions to identify rows",
            },
        },
        "required": ["table", "where"],
    },
}
