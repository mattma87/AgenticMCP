"""AgenticMCP server implementation with API and direct SQL support."""

import asyncio
import json
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import get_api_client, APIClient
from .config import get_settings

# Create server instance
server = Server("agenticmcp-postgres")

# Determine mode
API_MODE = os.getenv("MCP_API_URL") is not None or os.getenv("MCP_JWT_TOKEN") is not None

# Initialize API client if in API mode
_api_client: APIClient | None = None


async def get_client():
    """Get API client (only in API mode)."""
    global _api_client
    if API_MODE:
        if _api_client is None:
            _api_client = get_api_client()
        return _api_client
    return None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools based on current mode."""
    tools = []

    if API_MODE:
        # API mode tools
        tools.extend([
            Tool(
                name="list_endpoints",
                description="List all available API endpoints",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_token_info",
                description="Get information about the current JWT token",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="api_get",
                description="Make a GET request to an API endpoint",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "API endpoint path (e.g., /api/v1/users)",
                        },
                        "params": {
                            "type": "object",
                            "description": "Query parameters",
                        },
                    },
                    "required": ["endpoint"],
                },
            ),
            Tool(
                name="api_post",
                description="Make a POST request to an API endpoint",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "API endpoint path (e.g., /api/v1/users)",
                        },
                        "data": {
                            "type": "object",
                            "description": "Request body data",
                        },
                    },
                    "required": ["endpoint", "data"],
                },
            ),
            # Convenience methods for common endpoints
            Tool(
                name="list_users",
                description="List users (with optional search and pagination)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skip": {"type": "integer", "default": 0},
                        "limit": {"type": "integer", "default": 100},
                        "search": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="get_user",
                description="Get a specific user by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                    },
                    "required": ["user_id"],
                },
            ),
            Tool(
                name="list_products",
                description="List products (with optional filters)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skip": {"type": "integer", "default": 0},
                        "limit": {"type": "integer", "default": 100},
                        "search": {"type": "string"},
                        "min_price": {"type": "number"},
                        "max_price": {"type": "number"},
                        "in_stock": {"type": "boolean"},
                    },
                },
            ),
            Tool(
                name="get_product",
                description="Get a specific product by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                    },
                    "required": ["product_id"],
                },
            ),
            Tool(
                name="list_orders",
                description="List orders (with optional filters)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skip": {"type": "integer", "default": 0},
                        "limit": {"type": "integer", "default": 100},
                        "status": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="get_order",
                description="Get a specific order by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "integer"},
                    },
                    "required": ["order_id"],
                },
            ),
        ])
    else:
        # Direct SQL mode (legacy - for backward compatibility)
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
        from .permissions import get_permissions_checker

        perm_checker = get_permissions_checker()

        # Admin-only tools
        if perm_checker.can_execute_raw_query():
            tools.append(Tool(**query_tool_definition))

        # Table management tools
        tools.extend([
            Tool(**list_tables_tool_definition),
            Tool(**describe_table_tool_definition),
            Tool(**select_tool_definition),
            Tool(**insert_tool_definition),
            Tool(**update_tool_definition),
            Tool(**delete_tool_definition),
        ])

        tools.append(Tool(
            name="get_role_info",
            description="Get information about the current role and permissions",
            inputSchema={"type": "object", "properties": {}},
        ))

    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if API_MODE:
            return await handle_api_tool(name, arguments)
        else:
            return await handle_sql_tool(name, arguments)
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": str(e)})
        )]


async def handle_api_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle API mode tool calls."""
    client = await get_client()

    if name == "list_endpoints":
        result = await client.get_endpoints()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_token_info":
        result = await client.get_token_info()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "api_get":
        endpoint = arguments.get("endpoint", "")
        params = arguments.get("params")
        result = await client.get(endpoint, params)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "api_post":
        endpoint = arguments.get("endpoint", "")
        data = arguments.get("data", {})
        result = await client.post(endpoint, data)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "list_users":
        result = await client.list_users(
            skip=arguments.get("skip", 0),
            limit=arguments.get("limit", 100),
            search=arguments.get("search"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_user":
        user_id = arguments.get("user_id")
        result = await client.get_user(user_id)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "list_products":
        result = await client.list_products(
            skip=arguments.get("skip", 0),
            limit=arguments.get("limit", 100),
            search=arguments.get("search"),
            min_price=arguments.get("min_price"),
            max_price=arguments.get("max_price"),
            in_stock=arguments.get("in_stock", False),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_product":
        product_id = arguments.get("product_id")
        result = await client.get_product(product_id)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "list_orders":
        result = await client.list_orders(
            skip=arguments.get("skip", 0),
            limit=arguments.get("limit", 100),
            status=arguments.get("status"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_order":
        order_id = arguments.get("order_id")
        result = await client.get_order(order_id)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": f"Unknown tool: {name}"})
        )]


async def handle_sql_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle direct SQL mode tool calls (legacy)."""
    from .tools import TablesTool
    from .tools.query import QueryTool

    query_tool = QueryTool()
    tables_tool = TablesTool()

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
        from .permissions import get_permissions_checker
        perm_checker = get_permissions_checker()
        result = {
            "success": True,
            "role_info": perm_checker.get_permission_summary(),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "reload_permissions":
        from .permissions import reload_permissions_checker
        reload_permissions_checker()
        from .permissions import get_permissions_checker
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


async def main() -> None:
    """Main entry point for the server."""
    import sys

    if API_MODE:
        print(f"🚀 Starting AgenticMCP in API mode", file=sys.stderr)
        api_url = os.getenv("MCP_API_URL", "http://localhost:8000")
        print(f"📡 API URL: {api_url}", file=sys.stderr)
    else:
        print(f"🚀 Starting AgenticMCP in SQL mode", file=sys.stderr)
        settings = get_settings()
        print(f"📦 Database: {settings.db_host}:{settings.db_port}/{settings.db_name}", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
