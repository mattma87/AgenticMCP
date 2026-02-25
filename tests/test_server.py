"""Tests for the AgenticMCP server."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.types import TextContent

from agenticmcp.server import call_tool, list_tools


@pytest.mark.asyncio
async def test_list_tools() -> None:
    """Test that list_tools returns the expected tools."""
    tools = await list_tools()

    assert len(tools) == 2

    # Check echo tool
    echo_tool = next((t for t in tools if t.name == "echo"), None)
    assert echo_tool is not None
    assert echo_tool.description == "Echo back the input text"
    assert "text" in echo_tool.inputSchema["properties"]
    assert echo_tool.inputSchema["required"] == ["text"]

    # Check get_time tool
    time_tool = next((t for t in tools if t.name == "get_time"), None)
    assert time_tool is not None
    assert time_tool.description == "Get the current time"
    assert "timezone" in time_tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_call_tool_echo() -> None:
    """Test the echo tool."""
    result = await call_tool("echo", {"text": "Hello, World!"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Echo: Hello, World!"


@pytest.mark.asyncio
async def test_call_tool_get_time() -> None:
    """Test the get_time tool."""
    result = await call_tool("get_time", {"timezone": "UTC"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text.startswith("Current time in UTC:")


@pytest.mark.asyncio
async def test_call_tool_get_time_default_timezone() -> None:
    """Test the get_time tool with default timezone."""
    result = await call_tool("get_time", {})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_call_tool_unknown() -> None:
    """Test calling an unknown tool."""
    result = await call_tool("unknown_tool", {})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert result[0].text == "Unknown tool: unknown_tool"
