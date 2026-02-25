# AgenticMCP

An agentic Model Context Protocol (MCP) server built with Python.

## Overview

AgenticMCP is an MCP server that provides tools for AI agents to interact with. It implements the [Model Context Protocol](https://modelcontextprotocol.io/) specification.

## Installation

```bash
pip install -e .
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running

```bash
# Run the server
agenticmcp
```

Or with MCP client configuration:

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

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=agenticmcp
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Available Tools

- `echo`: Echo back the input text
- `get_time`: Get the current time in a specified timezone

## License

MIT
