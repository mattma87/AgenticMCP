"""AgenticMCP server implementation with PostgreSQL support."""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import get_settings, get_permissions
from .database import get_db, close_db
from .permissions import get_permissions_checker
from .tools import TablesTool
from .tools.query import QueryTool, query_tool_definition
from .tools.tables import (
    list_tables_tool_definition,
    describe_table_tool_definition,
    select_tool_definition,
    insert_tool_definition,
    update_tool_definition,
    delete_tool_definition,
)

# Create server instance
server = Server("agenticmcp-postgres")

# Initialize tools
query_tool = QueryTool()
tables_tool = TablesTool()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools based on current permissions."""
    perm_checker = get_permissions_checker()
    tools = []

    # Admin-only tools
    if perm_checker.can_execute_raw_query():
        tools.append(Tool(**query_tool_definition))

    # Table management tools (always available, permissions checked per-operation)
    tools.extend([
        Tool(**list_tables_tool_definition),
        Tool(**describe_table_tool_definition),
        Tool(**select_tool_definition),
        Tool(**insert_tool_definition),
        Tool(**update_tool_definition),
        Tool(**delete_tool_definition),
    ])

    # System tools
    tools.append(
        Tool(
            name="get_role_info",
            description="Get information about the current role and permissions",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    )

    tools.append(
        Tool(
            name="reload_permissions",
            description="Reload the permissions configuration from file",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    )

    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "query":
            result = await query_tool.execute(
                sql=arguments.get("sql", ""),
                params=arguments.get("params"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_tables":
            result = await tables_tool.list_tables()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "describe_table":
            result = await tables_tool.describe_table(
                table_name=arguments.get("table", "")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "select":
            result = await tables_tool.select(
                table=arguments.get("table", ""),
                columns=arguments.get("columns"),
                where=arguments.get("where"),
                order_by=arguments.get("order_by"),
                limit=arguments.get("limit"),
                offset=arguments.get("offset", 0),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "insert":
            result = await tables_tool.insert(
                table=arguments.get("table", ""),
                data=arguments.get("data", {}),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "update":
            result = await tables_tool.update(
                table=arguments.get("table", ""),
                data=arguments.get("data", {}),
                where=arguments.get("where", {}),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "delete":
            result = await tables_tool.delete(
                table=arguments.get("table", ""),
                where=arguments.get("where", {}),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_role_info":
            perm_checker = get_permissions_checker()
            result = {
                "success": True,
                "role_info": perm_checker.get_permission_summary(),
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "reload_permissions":
            from .permissions import reload_permissions_checker
            reload_permissions_checker()
            perm_checker = get_permissions_checker()
            result = {
                "success": True,
                "message": "Permissions reloaded",
                "role_info": perm_checker.get_permission_summary(),
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Unknown tool: {name}"})
            )]

    except PermissionError as e:
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": f"Permission denied: {e}"})
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": str(e)})
        )]


async def main() -> None:
    """Main entry point for the server."""
    settings = get_settings()

    # Log startup info (to stderr so it doesn't interfere with stdio)
    import sys
    print(f"Starting AgenticMCP PostgreSQL server", file=sys.stderr)
    print(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}", file=sys.stderr)
    print(f"Role: {settings.role}", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

    # Cleanup
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
