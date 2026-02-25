"""Generic SQL query tool (admin only)."""

import json
from typing import Any

from ..database import get_db
from ..permissions import get_permissions_checker


class QueryTool:
    """Generic SQL query tool with permission checking."""

    def __init__(self) -> None:
        """Initialize the query tool."""
        self.db = get_db()
        self.perm_checker = get_permissions_checker()

    async def execute(
        self,
        sql: str,
        params: list[Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a raw SQL query (admin only).

        Args:
            sql: SQL query with placeholders ($1, $2, etc.)
            params: Query parameters

        Returns:
            Query results as JSON

        Raises:
            PermissionError: If user doesn't have admin privileges
        """
        # Check permission
        self.perm_checker.check_permission("query", "")

        # Validate SQL - only allow SELECT statements
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            raise PermissionError(
                "Only SELECT queries are allowed for security reasons"
            )

        try:
            results = await self.db.execute_query(sql, params)

            # Format results for JSON serialization
            formatted = self._format_results(results)

            return {
                "success": True,
                "count": len(results) if isinstance(results, list) else 0,
                "data": formatted,
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
        # Handle datetime objects
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


# Tool definition for MCP
query_tool_definition = {
    "name": "query",
    "description": "Execute a raw SQL SELECT query (admin only). "
    "Uses PostgreSQL placeholders ($1, $2, etc.) for parameters.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "SQL SELECT query with placeholders ($1, $2, etc.)",
            },
            "params": {
                "type": "array",
                "description": "Query parameters matching placeholders",
                "items": {"type": "string"},
            },
        },
        "required": ["sql"],
    },
}
