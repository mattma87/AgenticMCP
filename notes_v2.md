# Notes: AgenticMCP v2 - API Layer Architecture

## Architecture Decision: API Layer vs Direct SQL

### Why API Layer?

| Concern | Direct SQL | API Layer |
|---------|-----------|-----------|
| **数据安全** | SQL注入风险，难以管控 | 集中验证，可控的数据暴露 |
| **权限控制** | 分散在各个工具 | API中间件统一处理 |
| **Token认证** | 环境变量，不安全 | JWT标准，可撤销 |
| **数据脱敏** | 手动处理每个查询 | API响应自动处理 |
| **审计日志** | 难以实现统一记录 | 每个请求自动记录 |
| **业务逻辑** | 混在MCP工具中 | 分离到API服务层 |
| **可复用性** | 仅MCP可用 | 任何HTTP客户端 |

### Data Exposure Strategy

#### Direct SQL (Current - INSECURE for production)
```python
# Anyone with "reader" role can query
await db.execute("SELECT * FROM users WHERE id = $1", [user_id])
# Problem: What if they query sensitive data?
```

#### API Endpoint (New - SECURE)
```python
@router.get("/api/v1/users/{user_id}")
async def get_user(user_id: int, auth: AuthContext = Depends(verify_token)):
    # Explicit data definition
    user = await user_service.get_user(user_id, auth.user_id, auth.role)
    # Data masking applied based on role
    return user_service.mask_sensitive_fields(user, auth.role)
```

## JWT Token Authentication

### Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 123,
    "role": "reader",
    "tenant_id": 1,
    "exp": 1706140800,
    "iat": 1706137200
  }
}
```

### Token Generation
```python
def create_token(user_id: int, role: str, tenant_id: int) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### Token Validation (FastAPI Middleware)
```python
async def verify_token(authorization: str = Header(...)) -> AuthContext:
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return AuthContext(
            user_id=payload["user_id"],
            role=payload["role"],
            tenant_id=payload["tenant_id"]
        )
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

### Token Validation (MCP Server)
```python
# MCP gets token from environment
token = os.getenv("MCP_JWT_TOKEN")
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
# Use payload to make API requests
headers = {"Authorization": f"Bearer {token}"}
```

## Data Masking Strategy

### Masking Rules Configuration
```yaml
# config/masking_rules.yaml
rules:
  email:
    admin: full           # admin@example.com
    support: partial      # a***@example.com
    reader: hidden        # [REDACTED]

  phone:
    admin: full           # +1234567890
    support: partial      # +123***7890
    reader: hidden        # [REDACTED]

  ssn:
    admin: full           # 123-45-6789
    support: partial      # ***-**-6789
    reader: hidden        # [REDACTED]

  credit_card:
    admin: full           # 4111111111111111
    support: partial      # 4111********1111
    reader: hidden        # [REDACTED]
```

### Implementation
```python
class DataMaskingService:
    def mask_field(self, field_name: str, value: str, role: str) -> str:
        rule = masking_rules.get(field_name, {})
        strategy = rule.get(role, "hidden")

        if strategy == "full":
            return value
        elif strategy == "partial":
            return self._partial_mask(field_name, value)
        else:  # hidden
            return "[REDACTED]"

    def _partial_mask(self, field_name: str, value: str) -> str:
        if field_name == "email":
            user, domain = value.split("@")
            return f"{user[0]}***@{domain}"
        elif field_name == "phone":
            return f"{value[:4]}***{value[-4:]}"
        # ... more patterns
```

## API Endpoint Design

### Endpoint: GET /api/v1/users
```python
@router.get("/api/v1/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    auth: AuthContext = Depends(verify_token)
):
    # Check permissions
    if not auth.can_access("users", "read"):
        raise HTTPException(403, "Forbidden")

    # Apply row filter
    row_filter = None
    if auth.role != "admin":
        row_filter = {"tenant_id": auth.tenant_id}

    # Query with filters
    users = await user_repo.list(skip=skip, limit=limit, search=search, row_filter=row_filter)

    # Mask sensitive data
    masked_users = [
        masking_service.mask_user(user, auth.role)
        for user in users
    ]

    # Log access
    await audit_logger.log(
        user_id=auth.user_id,
        action="list_users",
        params={"skip": skip, "limit": limit},
        result_count=len(masked_users)
    )

    return {"users": masked_users, "count": len(masked_users)}
```

### Endpoint: GET /api/v1/users/{id}
```python
@router.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    auth: AuthContext = Depends(verify_token)
):
    # Check permissions
    if not auth.can_access("users", "read"):
        raise HTTPException(403, "Forbidden")

    # Non-admin can only see themselves
    if auth.role != "admin" and auth.user_id != user_id:
        raise HTTPException(403, "You can only view your own profile")

    # Get user
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Mask data
    masked_user = masking_service.mask_user(user, auth.role)

    # Log access
    await audit_logger.log(
        user_id=auth.user_id,
        action="get_user",
        target_id=user_id,
    )

    return masked_user
```

## Audit Logging

### Audit Log Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    tenant_id INTEGER,
    action TEXT NOT NULL,
    endpoint TEXT,
    params JSONB,
    target_id INTEGER,
    result_count INTEGER,
    status TEXT, -- 'success', 'error'
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### Audit Logger Service
```python
class AuditLogger:
    async def log(
        self,
        user_id: int,
        role: str,
        action: str,
        endpoint: str | None = None,
        params: dict | None = None,
        target_id: int | None = None,
        result_count: int | None = None,
        status: str = "success",
        error_message: str | None = None
    ):
        await db.execute(
            """INSERT INTO audit_logs
            (user_id, role, action, endpoint, params, target_id, result_count, status, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            user_id, role, action, endpoint, params, target_id, result_count, status, error_message
        )
```

## MCP Server (Refactored)

### New MCP Tools
```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_endpoints",
            description="List available API endpoints",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="call_endpoint",
            description="Call an API endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "path": {"type": "string"},
                    "params": {"type": "object"}
                },
                "required": ["method", "path"]
            }
        ),
        Tool(
            name="get_token_info",
            description="Get current JWT token information",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]
```

### API Client
```python
class APIClient:
    def __init__(self):
        self.base_url = os.getenv("MCP_API_URL", "http://localhost:8000")
        self.token = os.getenv("MCP_JWT_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def call(self, method: str, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=self.headers, json=params)
            # ... other methods
        return response.json()
```

## Migration Plan

### Phase 1: Keep Existing, Add Backend
- Keep current MCP server running
- Add FastAPI backend alongside
- Both connect to same database
- Gradually migrate features

### Phase 2: Dual Mode MCP Server
- Add MCP_API_URL environment variable
- If set, use API mode
- If not set, use direct SQL mode (current)

### Phase 3: API-Only Mode
- Remove direct SQL access
- All MCP tools use API
- Deprecate old tools

### Phase 4: Complete Migration
- Remove old code
- API-only architecture
- Add more endpoints as needed

## Security Checklist

- [ ] JWT token with expiration
- [ ] Token refresh mechanism
- [ ] Password hashing (bcrypt)
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] SQL injection prevention (parameterized queries)
- [ ] Data masking for sensitive fields
- [ ] Audit logging for all access
- [ ] HTTPS in production
- [ ] Environment variable for secrets
- [ ] Regular security updates

## Sources

- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- JWT in Python: https://pyjwt.readthedocs.io/
- OWASP API Security: https://owasp.org/www-project-api-security/
