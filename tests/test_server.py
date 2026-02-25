"""Tests for the AgenticMCP PostgreSQL server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import TextContent

from agenticmcp.server import call_tool, list_tools


@pytest.mark.asyncio
async def test_list_tools_reader_role() -> None:
    """Test that list_tools returns expected tools for reader role."""
    with patch('agenticmcp.server.get_permissions_checker') as mock_perm:
        mock_checker = MagicMock()
        mock_checker.can_execute_raw_query.return_value = False
        mock_perm.return_value = mock_checker

        tools = await list_tools()

        # Should have all tools except query (admin-only)
        tool_names = {t.name for t in tools}
        assert "query" not in tool_names
        assert "list_tables" in tool_names
        assert "describe_table" in tool_names
        assert "select" in tool_names
        assert "insert" in tool_names
        assert "update" in tool_names
        assert "delete" in tool_names
        assert "get_role_info" in tool_names
        assert "reload_permissions" in tool_names


@pytest.mark.asyncio
async def test_list_tools_admin_role() -> None:
    """Test that list_tools returns query tool for admin role."""
    with patch('agenticmcp.server.get_permissions_checker') as mock_perm:
        mock_checker = MagicMock()
        mock_checker.can_execute_raw_query.return_value = True
        mock_perm.return_value = mock_checker

        tools = await list_tools()

        # Should have all tools including query
        tool_names = {t.name for t in tools}
        assert "query" in tool_names
        assert "list_tables" in tool_names


@pytest.mark.asyncio
async def test_call_tool_get_role_info() -> None:
    """Test the get_role_info tool."""
    with patch('agenticmcp.server.get_permissions_checker') as mock_perm:
        mock_checker = MagicMock()
        mock_checker.get_permission_summary.return_value = {
            "role": "reader",
            "tables": ["users", "products"],
            "operations": ["read"],
        }
        mock_perm.return_value = mock_checker

        result = await call_tool("get_role_info", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["role_info"]["role"] == "reader"


@pytest.mark.asyncio
async def test_call_tool_reload_permissions() -> None:
    """Test the reload_permissions tool."""
    from agenticmcp.permissions import reload_permissions_checker
    with patch('agenticmcp.permissions.reload_permissions_checker') as mock_reload:
        with patch('agenticmcp.server.get_permissions_checker') as mock_perm:
            mock_checker = MagicMock()
            mock_checker.get_permission_summary.return_value = {"role": "reader"}
            mock_perm.return_value = mock_checker

            result = await call_tool("reload_permissions", {})

            mock_reload.assert_called_once()

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["success"] is True


@pytest.mark.asyncio
async def test_call_tool_unknown() -> None:
    """Test calling an unknown tool."""
    result = await call_tool("unknown_tool", {})

    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["success"] is False
    assert "Unknown tool" in data["error"]
