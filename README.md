# AgenticMCP - PostgreSQL MCP Server

A Model Context Protocol (MCP) server that provides secure, role-based access to PostgreSQL databases for AI agents.

## Features

- **PostgreSQL Integration**: Connect to any PostgreSQL database
- **Role-Based Access Control (RBAC)**: Fine-grained permissions at table, column, and row levels
- **Safe Query Building**: All queries use parameterized statements to prevent SQL injection
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **CI/CD Ready**: GitHub Actions workflows included
- **Multiple MCP Tools**: Comprehensive tools for database operations

## Available MCP Tools

| Tool | Description | Permission Required |
|------|-------------|---------------------|
| `list_tables` | List all accessible tables | Any role |
| `describe_table` | Get table schema | Read access |
| `select` | Query data with filtering, sorting, pagination | Read access |
| `insert` | Insert new rows | Write access |
| `update` | Update existing rows | Write access |
| `delete` | Delete rows | Write access |
| `query` | Execute raw SQL SELECT | Admin only |
| `get_role_info` | Get current role and permissions | Any role |
| `reload_permissions` | Reload permissions configuration | Any role |

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/AgenticMCP.git
cd AgenticMCP

# Start PostgreSQL and the MCP server
docker compose -f docker/docker-compose.yml up -d

# Check logs
docker compose -f docker/docker-compose.yml logs -f
```

This will start:
- PostgreSQL on port 5432
- Sample database with test data
- MCP server instances for different roles

### 2. Local Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install with dependencies
pip install -e ".[dev]"

# Set environment variables
export MCP_DB_HOST=localhost
export MCP_DB_PORT=5432
export MCP_DB_NAME=app_db
export MCP_DB_USER=app_user
export MCP_DB_PASSWORD=your_password
export MCP_ROLE=reader

# Run the server
agenticmcp
```

### 3. Using Docker Image

```bash
# Pull the image
docker pull ghcr.io/YOUR_USERNAME/agenticmcp:latest

# Run the server
docker run -i --rm \
  -e MCP_DB_HOST=host.docker.internal \
  -e MCP_DB_PORT=5432 \
  -e MCP_DB_NAME=app_db \
  -e MCP_DB_USER=app_user \
  -e MCP_DB_PASSWORD=your_password \
  -e MCP_ROLE=reader \
  -v $(pwd)/config:/app/config:ro \
  ghcr.io/YOUR_USERNAME/agenticmcp:latest
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_DB_HOST` | PostgreSQL host | localhost |
| `MCP_DB_PORT` | PostgreSQL port | 5432 |
| `MCP_DB_NAME` | Database name | postgres |
| `MCP_DB_USER` | Database user | postgres |
| `MCP_DB_PASSWORD` | Database password | (empty) |
| `MCP_ROLE` | Role for access control | reader |
| `MCP_USER_ID` | User ID for row-level security | (optional) |
| `MCP_TENANT_ID` | Tenant ID for multi-tenant | (optional) |
| `MCP_PERMISSIONS_FILE` | Path to permissions.yaml | config/permissions.yaml |
| `MCP_MAX_QUERY_ROWS` | Maximum rows per query | 1000 |
| `MCP_QUERY_TIMEOUT` | Query timeout in seconds | 30 |

### Permissions Configuration

Edit `config/permissions.yaml` to define roles and access:

```yaml
version: "1.0"
default_role: "reader"

roles:
  admin:
    description: "Full administrative access"
    tables: ["*"]
    operations: ["*"]

  reader:
    description: "Read-only access"
    tables: ["users", "products"]
    operations: ["read"]
    columns:
      users: ["id", "name"]  # Exclude sensitive columns

  writer:
    description: "Read and write access"
    tables: ["users", "orders"]
    operations: ["read", "write"]
    row_filters:
      orders: "user_id = {user_id}"  # Row-level security

tables:
  users:
    primary_key: "id"
    columns:
      - name: id
        type: "integer"
      - name: email
        type: "text"
        sensitive: true
        visible_to: ["admin"]
```

## Client Configuration

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agenticmcp-postgres": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_DB_HOST=host.docker.internal",
        "-e", "MCP_DB_PORT=5432",
        "-e", "MCP_DB_NAME=app_db",
        "-e", "MCP_DB_USER=app_user",
        "-e", "MCP_DB_PASSWORD=your_password",
        "-e", "MCP_ROLE=reader",
        "ghcr.io/YOUR_USERNAME/agenticmcp:latest"
      ]
    }
  }
}
```

See `examples/claude_desktop_config.json` for more examples.

### MCP Inspector

```bash
# Start the server
agenticmcp

# In another terminal, run inspector
npx @modelcontextprotocol/inspector
```

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=agenticmcp

# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

### Database Initialization

The `docker/init.sql` file creates sample tables for testing:

- `users` - User accounts
- `products` - Product catalog
- `orders` - Orders with status
- `order_items` - Order line items
- `analytics` - Analytics metrics

## CI/CD

### GitHub Actions

The project includes two workflows:

**CI Workflow** (`.github/workflows/ci.yml`):
- Runs on push and pull requests
- Executes linting, type checking, and tests
- Builds Docker image

**Release Workflow** (`.github/workflows/release.yml`):
- Triggers on version tags (`v*.*.*`)
- Builds and pushes Docker image to GHCR
- Creates GitHub release

### Manual Docker Build

```bash
# Build the image
docker build -f docker/Dockerfile -t agenticmcp:test .

# Run the container
docker run -i --rm \
  -e MCP_DB_HOST=host.docker.internal \
  -e MCP_DB_NAME=app_db \
  -e MCP_ROLE=admin \
  agenticmcp:test
```

## Security

- **SQL Injection Prevention**: All queries use parameterized statements
- **Row-Level Security**: Support for WHERE clause injection based on user context
- **Column-Level Filtering**: Sensitive columns can be hidden from specific roles
- **Admin-Only Raw Queries**: Raw SQL execution restricted to admin role
- **Connection Pooling**: Efficient database connection management

## Project Structure

```
agenticmcp/
├── src/agenticmcp/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── database.py        # Database connection and queries
│   ├── permissions.py     # Access control system
│   ├── config.py          # Configuration management
│   └── tools/             # MCP tool implementations
├── config/
│   └── permissions.yaml   # Role and table permissions
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── init.sql           # Sample database schema
├── .github/workflows/
│   ├── ci.yml             # Continuous Integration
│   └── release.yml        # Release automation
├── examples/
│   ├── claude_desktop_config.json
│   └── inspector_config.json
└── tests/
    ├── test_server.py
    ├── test_database.py
    └── test_permissions.py
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.
