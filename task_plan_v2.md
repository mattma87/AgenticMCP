# Task Plan: AgenticMCP v2 - API Layer Architecture

## Goal
重构 AgenticMCP 为双层架构：MCP Server + FastAPI Backend，实现集中式的数据管控、JWT认证和审计日志。

Refactor AgenticMCP to a two-layer architecture: MCP Server + FastAPI Backend, implementing centralized data control, JWT authentication, and audit logging.

## Architecture Decision: **API Layer Pattern**

### Why API Layer?
| Aspect | Direct SQL (Current) | API Layer (New) |
|--------|---------------------|-----------------|
| Data Control | Scattered in tools | Centralized in endpoints |
| Auth | Environment-based | JWT-based |
| Data Masking | Manual per query | Automatic in API response |
| Audit | Hard to track | Central logging |
| Reusability | MCP-only | Any HTTP client |
| Maintenance | Business logic in MCP | Separation of concerns |

### New Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Client                           │
└─────────────────────────────┬───────────────────────────────┘
                              │ JWT Token via MCP_CONFIG
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                               │
│  - Token validation on startup                              │
│  - Discover available endpoints from API                    │
│  - Tools: list_endpoints, call_endpoint                     │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP (localhost:8000)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  JWT Authentication Middleware                     │    │
│  │  - Token validation on each request               │    │
│  │  - User context (id, role, tenant)                │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  API Endpoints (Data Services)                     │    │
│  │  - /api/v1/users/{id}                             │    │
│  │  - /api/v1/products                               │    │
│  │  - /api/v1/orders                                 │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Business Services                                 │    │
│  │  - Data validation                                 │    │
│  │  - Data masking                                    │    │
│  │  - Row-level security                              │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Audit Logger                                      │    │
│  │  - All requests logged                             │    │
│  │  - User, endpoint, timestamp, result               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    PostgreSQL Database
```

## Phases

- [ ] Phase 1: 架构设计与规划 (Architecture Design)
- [ ] Phase 2: FastAPI 后端实现 (FastAPI Backend)
  - [ ] 2.1 项目结构重构
  - [ ] 2.2 JWT 认证系统
  - [ ] 2.3 API 端点实现
  - [ ] 2.4 数据服务层
- [ ] Phase 3: 数据管控与验证 (Data Control)
  - [ ] 3.1 数据验证 (Pydantic schemas)
  - [ ] 3.2 数据脱敏 (Data masking)
  - [ ] 3.3 行级安全 (Row-level security)
  - [ ] 3.4 审计日志 (Audit logging)
- [ ] Phase 4: MCP Server 重构 (MCP Server Refactor)
  - [ ] 4.1 移除直接数据库访问
  - [ ] 4.2 实现 API 调用工具
  - [ ] 4.3 Token 认证集成
  - [ ] 4.4 端点发现机制
- [ ] Phase 5: Token 管理 (Token Management)
  - [ ] 5.1 Token 生成 API
  - [ ] 5.2 Token 刷新机制
  - [ ] 5.3 Token 吊销 (可选 Redis)
  - [ ] 5.4 管理界面/CLI
- [ ] Phase 6: 测试与文档 (Testing & Documentation)
- [ ] Phase 7: Docker 与部署 (Docker & Deployment)
- [ ] Phase 8: 迁移与兼容性 (Migration & Compatibility)

## Key Decisions

### Decision 1: 移除通用 SQL 查询
- **原因**: 安全风险，难以管控
- **替代**: 预定义的 API 端点
- **结果**: 所有数据访问都是显式的、可审计的

### Decision 2: JWT Token 认证
- **位置**: FastAPI 中间件
- **Claims**: user_id, role, tenant_id, exp
- **传递方式**: MCP 通过环境变量传递 Token

### Decision 3: 数据脱敏在 API 层
- **敏感字段**: email, phone, ssn, credit_card
- **配置**: permissions.yaml 定义敏感字段
- **策略**:
  - admin: 完整数据
  - support: 部分遮蔽 (a***@example.com)
  - reader: 完全隐藏

### Decision 4: 审计日志
- **记录**: 每个API调用
- **内容**: user_id, endpoint, params, timestamp, result
- **存储**: 数据库表 (audit_logs)
- **保留**: 可配置保留期

## File Structure (New)

```
agenticmcp/
├── backend/                      # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Backend config
│   ├── dependencies.py           # FastAPI dependencies
│   │
│   ├── auth/                     # Authentication
│   │   ├── __init__.py
│   │   ├── jwt.py                # JWT token handling
│   │   ├── middleware.py         # Auth middleware
│   │   └── models.py             # User, Token models
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── v1/                   # API v1
│   │   │   ├── __init__.py
│   │   │   ├── users.py          # User endpoints
│   │   │   ├── products.py       # Product endpoints
│   │   │   ├── orders.py         # Order endpoints
│   │   │   ├── analytics.py      # Analytics endpoints
│   │   │   └── auth.py           # Token endpoints
│   │   └── dependencies.py       # Route dependencies
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   └── data_masking.py       # Data masking logic
│   │
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py               # User schemas
│   │   ├── product.py            # Product schemas
│   │   ├── order.py              # Order schemas
│   │   └── audit.py              # Audit log schema
│   │
│   ├── database/                 # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py         # Database connection
│   │   ├── repositories/         # Repository pattern
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── product_repo.py
│   │   │   └── order_repo.py
│   │   └── migrations/           # DB migrations
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py             # Audit logger
│       └── validators.py         # Custom validators
│
├── src/agenticmcp/               # MCP Server (Refactored)
│   ├── __init__.py
│   ├── server.py                 # MCP server (simplified)
│   ├── config.py                 # MCP config
│   ├── client.py                 # HTTP client for API calls
│   └── tools/                    # MCP tools
│       ├── __init__.py
│       ├── discovery.py          # Endpoint discovery
│       └── caller.py             # Generic API caller
│
├── config/
│   ├── permissions.yaml          # Permissions config
│   ├── masking_rules.yaml        # Data masking rules
│   └── endpoints.yaml            # Endpoint definitions
│
├── docker/
│   ├── Dockerfile.mcp            # MCP server Dockerfile
│   ├── Dockerfile.backend        # Backend Dockerfile
│   └── docker-compose.yml        # Full stack
│
├── scripts/
│   ├── generate_token.py         # Token generation CLI
│   └── migrate_db.py             # DB migration script
│
├── tests/
│   ├── backend/                  # Backend tests
│   │   ├── test_auth.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_masking.py
│   └── mcp/                      # MCP tests
│       └── test_client.py
│
└── pyproject.toml
```

## API Endpoint Examples

### User Endpoints
```yaml
# GET /api/v1/users
- List users (with filtering, pagination)
- Permission: reader+
- Returns: id, name (email hidden for non-admin)

# GET /api/v1/users/{id}
- Get user by ID
- Permission: reader+
- Returns: User details (masked by role)

# POST /api/v1/users
- Create user
- Permission: admin only
- Body: name, email, password

# PUT /api/v1/users/{id}
- Update user
- Permission: admin or own user
- Body: fields to update
```

### Product Endpoints
```yaml
# GET /api/v1/products
- List products
- Permission: reader+
- Filters: category, min_price, max_price, in_stock

# GET /api/v1/products/{id}
- Get product details

# POST /api/v1/products
- Create product
- Permission: admin, writer
```

### Order Endpoints
```yaml
# GET /api/v1/orders
- List orders
- Permission: reader+
- Row filter: user_id = {user_id} for non-admin

# POST /api/v1/orders
- Create order
- Permission: writer, admin
```

## MCP Tool Changes

### Old (Direct SQL)
```python
@server.call_tool()
async def select(table: str, where: dict, ...):
    query = build_select_query(table, where)
    return await db.execute(query)
```

### New (API Call)
```python
@server.call_tool()
async def call_api(endpoint: str, params: dict):
    # endpoint = "GET /api/v1/users"
    response = await http_client.get(
        f"http://localhost:8000{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )
    return response.json()
```

### New MCP Tools
1. `list_endpoints` - List available API endpoints
2. `call_endpoint` - Call an API endpoint
3. `get_token_info` - Get current token information
4. `refresh_token` - Refresh JWT token

## Token Management

### Token Generation CLI
```bash
# Generate token for user
python scripts/generate_token.py --user-id 123 --role reader --tenant 1

# Output:
# JWT Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Expires: 2025-01-25T10:30:00Z
```

### Token in MCP Config
```json
{
  "mcpServers": {
    "agenticmcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
        "-e", "MCP_API_URL=http://backend:8000",
        "-e", "MCP_JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      ]
    }
  }
}
```

## Status
**Currently in Phase 1** - 架构设计与规划

## Dependencies

### New Dependencies
```toml
dependencies = [
    # Existing
    "mcp>=0.9.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",

    # New for API Backend
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",            # Password hashing
    "python-multipart>=0.0.6",            # Form data
    "httpx>=0.25.0",                      # HTTP client for MCP
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "httpx>=0.25.0",                      # For testing API
]
```

## Errors Encountered
*None yet*

## Next Steps

1. **User Confirmation**: Confirm API layer architecture
2. **Phase 2.1**: Create new directory structure
3. **Phase 2.2**: Implement JWT authentication
4. **Phase 2.3**: Create first API endpoints
5. **Phase 4**: Refactor MCP server to use API
