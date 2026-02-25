"""AgenticMCP server implementation."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Create server instance
server = Server("agenticmcp")

# Register available tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="echo",
            description="Echo back the input text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to echo back",
                    }
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="get_time",
            description="Get the current time",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York')",
                        "default": "UTC",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "echo":
        text = arguments.get("text", "")
        return [TextContent(type="text", text=f"Echo: {text}")]
    elif name == "get_time":
        from datetime import datetime, timezone

        tz = arguments.get("timezone", "UTC")
        try:
            import zoneinfo

            tz_info = zoneinfo.ZoneInfo(tz)
            now = datetime.now(tz_info)
            return [TextContent(type="text", text=f"Current time in {tz}: {now.isoformat()}")]
        except Exception:
            utc_now = datetime.now(timezone.utc)
            return [TextContent(type="text", text=f"Current UTC time: {utc_now.iso_format()}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main() -> None:
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
