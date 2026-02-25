# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgenticMCP is a Python-based Model Context Protocol (MCP) server. MCP is a protocol that allows AI assistants to interact with external tools and data sources through a standardized interface.

## Development Commands

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running the Server

```bash
# Run the MCP server via stdio
agenticmcp

# Or run directly with Python
python -m agenticmcp.server
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=agenticmcp
```

### Code Quality

```bash
# Format code
black src/

# Check linting
ruff check src/

# Type checking
mypy src/
```

## Architecture

The project follows a standard Python package structure:

- `src/agenticmcp/` - Main package directory
  - `server.py` - MCP server implementation with tool registration and handlers
  - `__init__.py` - Package initialization

The server uses the `mcp` library to implement the MCP protocol over stdio. Tools are registered using the `@server.list_tools()` decorator and handled via `@server.call_tool()`.

## Adding New Tools

To add a new tool:

1. Add the tool definition in `server.py` within the `list_tools()` function
2. Implement the tool's logic in the `call_tool()` function
3. Follow the MCP tool schema format for input validation

## MCP Integration

The server communicates via stdio and can be integrated with MCP clients using:

```json
{
  "mcpServers": {
    "agenticmcp": {
      "command": "uvx",
      "args": ["--from", "agenticmcp", "agenticmcp"]
    }
  }
}
```
