# Docker Deployment - AgenticMCP v2

## Quick Start

### Production Deployment

```bash
# Start all services
docker-compose -f docker/docker-compose-v2.yml up -d

# View logs
docker-compose -f docker/docker-compose-v2.yml logs -f

# Stop services
docker-compose -f docker/docker-compose-v2.yml down
```

Services:
- **PostgreSQL**: `localhost:5432`
- **FastAPI Backend**: `http://localhost:8000`
  - API: http://localhost:8000/api/v1
  - Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health
- **MCP Server**: Runs in API mode (configured via environment)

### Development Deployment

```bash
# Start with hot reload
docker-compose -f docker/docker-compose.dev.yml up -d

# Generate JWT tokens
make token
```

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose-v2.yml` | Production deployment |
| `docker-compose.dev.yml` | Development with hot reload |
| `Dockerfile.backend` | FastAPI backend image |
| `Dockerfile.mcp` | MCP server image |

## Environment Variables

### Backend Environment
```bash
BACKEND_DB_HOST=postgres
BACKEND_DB_PORT=5432
BACKEND_DB_NAME=agenticmcp
BACKEND_DB_USER=postgres
BACKEND_DB_PASSWORD=postgres
BACKEND_JWT_SECRET=your-secret-key
BACKEND_DEBUG=true
```

### MCP Client Environment
```bash
MCP_API_URL=http://localhost:8000
MCP_JWT_TOKEN=<your-jwt-token>
```

## Using MCP Client with Docker

### Option 1: Docker Run

```bash
# Generate token first
make token

# Run MCP client
docker run -i --rm \
  -e MCP_API_URL=http://backend:8000 \
  -e MCP_JWT_TOKEN=<token-from-above> \
  agenticmcp-mcp
```

### Option 2: Docker Compose Service

The `docker-compose-v2.yml` includes MCP server containers:
- `mcp-reader` - Pre-configured with reader role
- `mcp-admin` - Pre-configured with admin role

To use these services, you'll need to execute commands in the container:

```bash
# Enter the container
docker exec -it agenticmcp-mcp-reader bash

# Run MCP server
python -m agenticmcp.server
```

## JWT Token Management

### Generate Tokens

```bash
# Using make
make token

# Using Docker
docker-compose -f docker/docker-compose.dev.yml run --rm token-generator

# Using Python directly
python scripts/generate_token.py --user-id 1 --role admin
```

### Token Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access, can see all data including emails |
| `reader` | Read-only, emails masked as [REDACTED] |
| `writer` | Read and write, can create/edit own data |

## API Examples

### List Users (Admin)
```bash
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:8000/api/v1/users
```

### List Users (Reader)
```bash
curl -H "Authorization: Bearer <reader-token>" \
  http://localhost:8000/api/v1/users
```

Response:
```json
{
  "users": [
    {"name": "Alice Johnson", "email": "[REDACTED]", ...}
  ]
}
```

### Create Product (Admin/Writer)
```bash
curl -X POST \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 99.99, "stock": 10}' \
  http://localhost:8000/api/v1/products
```

## Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker-compose -f docker/docker-compose-v2.yml exec postgres \
  pg_isready -U postgres

# Service status
make ps
```

## Troubleshooting

### View Logs
```bash
# All services
make logs

# Specific service
make logs-backend
make logs-postgres
```

### Restart Services
```bash
make restart
```

### Rebuild Images
```bash
make rebuild
```

### Clean Everything
```bash
make clean
```

### Database Issues
```bash
# Reinitialize database
docker-compose -f docker/docker-compose-v2.yml down -v
docker-compose -f docker/docker-compose-v2.yml up -d
make init-db
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                              │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │  PostgreSQL  │     │ FastAPI      │     │  MCP Server  │  │
│  │  :5432       │────▶│ Backend      │────▶│  (API Mode)  │  │
│  │              │     │  :8000       │     │              │  │
│  └──────────────┘     └──────────────┘     └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Production Notes

1. **Change Secrets**: Update `BACKEND_JWT_SECRET` and `POSTGRES_PASSWORD` in production
2. **Persistent Data**: PostgreSQL data is stored in Docker volume
3. **Token Security**: Store JWT tokens securely; they grant access to your data
4. **Firewall**: Ensure ports 5432 and 8000 are properly secured in production
5. **Backups**: Regularly backup PostgreSQL data volume
