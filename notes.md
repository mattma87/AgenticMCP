# Notes: PostgreSQL MCP Server

## Architecture Decisions

### MCP Tool Design
The MCP server will expose the following tools:

1. **`query`** - Generic SQL query tool (admin only)
   ```json
   {
     "sql": "SELECT * FROM users WHERE id = $1",
     "params": [123]
   }
   ```

2. **`list_tables`** - List available tables for current role
3. **`describe_table`** - Get table schema
4. **`select`** - Read from table (with permissions)
5. **`insert`** - Insert into table (with permissions)
6. **`update`** - Update table rows (with permissions)
7. **`delete`** - Delete from table (with permissions)

### Permission Model

#### Role-Based Access Control (RBAC)
```yaml
roles:
  admin:
    permissions: ["*.*"]  # All tables, all operations
  reader:
    permissions: ["users:read", "products:read"]
  writer:
    permissions: ["users:read,write", "orders:read,write"]
  analytics:
    permissions: ["analytics:read"]
    row_filter: "tenant_id = {tenant_id}"
```

#### Table-Level Permissions
- `read` - SELECT access
- `write` - INSERT, UPDATE, DELETE access
- `*` - All operations

#### Column-Level Filtering
```yaml
tables:
  users:
    columns:
      - name: id
        visible_to: ["admin", "reader", "writer"]
      - name: email
        visible_to: ["admin"]
      - name: name
        visible_to: ["*"]
```

#### Row-Level Security
```yaml
tables:
  orders:
    row_filter:
      role: "writer"
      filter: "created_by = {user_id}"
```

## Configuration Schema

### config/permissions.yaml
```yaml
version: "1.0"

# Default role if none specified
default_role: "reader"

# Role definitions
roles:
  admin:
    description: "Full access to all tables"
    tables: ["*"]
    operations: ["*"]

  reader:
    description: "Read-only access"
    tables: ["users", "products"]
    operations: ["read"]
    columns:
      users: ["id", "name", "created_at"]  # Exclude sensitive fields

  writer:
    description: "Read and write access"
    tables: ["users", "orders"]
    operations: ["read", "write"]
    row_filters:
      orders: "created_by = {user_id}"

# Table schema definitions
tables:
  users:
    primary_key: "id"
    columns:
      - name: id
        type: "integer"
      - name: email
        type: "text"
        sensitive: true
      - name: name
        type: "text"
      - name: created_at
        type: "timestamp"

  products:
    primary_key: "id"
    columns:
      - name: id
        type: "integer"
      - name: name
        type: "text"
      - name: price
        type: "decimal"
      - name: stock
        type: "integer"
```

## Database Connection

### Connection String Format
```
postgresql://user:password@host:port/database
```

### Environment Variables
```bash
MCP_DB_HOST=localhost
MCP_DB_PORT=5432
MCP_DB_NAME=mydb
MCP_DB_USER=mcp_user
MCP_DB_PASSWORD=secret
MCP_DB_POOL_SIZE=10
MCP_PERMISSIONS_FILE=/app/config/permissions.yaml
MCP_ROLE=reader
MCP_USER_ID=optional_user_id  # For row-level security
```

## Docker Compose Structure

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  agenticmcp:
    build: .
    environment:
      MCP_DB_HOST: postgres
      MCP_DB_PORT: 5432
      MCP_DB_NAME: app_db
      MCP_DB_USER: app_user
      MCP_DB_PASSWORD: app_password
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./config:/app/config:ro
```

## MCP Client Configuration

### Claude Desktop Config
```json
{
  "mcpServers": {
    "postgres-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_DB_HOST=host.docker.internal",
        "-e", "MCP_DB_NAME=mydb",
        "-e", "MCP_DB_USER=myuser",
        "-e", "MCP_DB_PASSWORD=mypassword",
        "-e", "MCP_ROLE=reader",
        "-v", "${HOME}/.config/claude/permissions.yaml:/app/config/permissions.yaml:ro",
        "ghcr.io/user/agenticmcp:latest"
      ]
    }
  }
}
```

## CI/CD Pipeline

### CI Workflow (.github/workflows/ci.yml)
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: ruff check src/
      - run: black --check src/
      - run: mypy src/
      - run: pytest
```

### Release Workflow (.github/workflows/release.yml)
```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/user/agenticmcp:latest
```

## Research Sources

### MCP Documentation
- https://modelcontextprotocol.io/docs
- https://github.com/modelcontextprotocol/python-sdk

### PostgreSQL + Python
- asyncpg: https://github.com/magicstack/asyncpg
- SQLAlchemy: https://docs.sqlalchemy.org/

## Implementation Notes

### Security Considerations
1. Never allow raw SQL from non-admin roles
2. Use parameterized queries exclusively
3. Sanitize table/column names
4. Implement query timeout
5. Limit result set size

### Performance
1. Use connection pooling
2. Implement query result caching
3. Add pagination for large results
4. Use EXPLAIN ANALYZE for slow queries
