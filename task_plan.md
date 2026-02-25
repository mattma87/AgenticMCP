# Task Plan: PostgreSQL MCP Server with CI/CD

## Goal
创建一个完整的 MCP Server，通过 API 暴露 PostgreSQL 数据库数据，包含权限控制，支持 Docker 本地部署和 GitHub Actions CI/CD 流程。

Create a complete MCP Server that exposes PostgreSQL database data via API with permission control, supporting local Docker deployment and GitHub Actions CI/CD pipeline.

## Phases
- [x] Phase 1: 项目设计与架构 (Project Design & Architecture)
- [x] Phase 2: 数据库连接与模型 (Database Connection & Models)
- [x] Phase 3: MCP Server 实现 (MCP Server Implementation)
- [x] Phase 4: 权限控制系统 (Permission Control System)
- [x] Phase 5: 配置管理 (Configuration Management)
- [x] Phase 6: Docker 部署 (Docker Deployment)
- [x] Phase 7: GitHub Actions CI/CD (CI/CD Pipeline)
- [x] Phase 8: 测试与文档 (Testing & Documentation)
- [x] Phase 9: 示例与使用指南 (Examples & Usage Guide)

## Key Questions
1. **权限模型**: 如何实现权限控制？
   - 基于表的访问控制 (table-level ACL) ✓
   - 基于行的访问控制 (row-level security) ✓
   - 基于角色的访问控制 (RBAC) ✓

2. **API 设计**: MCP 工具应该如何设计？
   - 通用查询工具 (generic query tool) ✓
   - 预定义表的 CRUD 操作 ✓
   - 存储过程调用 (可选功能)

3. **部署方式**:
   - Docker Compose (包含 PostgreSQL) ✓
   - 环境变量配置 ✓
   - 密钥管理 ✓

## Decisions Made
- **权限模型**: 采用基于表的访问控制 + 基于角色的访问控制 (RBAC) ✓
- **数据库驱动**: 使用 `asyncpg` 进行异步 PostgreSQL 连接 ✓
- **配置方式**: 使用 YAML 配置文件定义表权限 ✓
- **MCP 工具**: 提供通用查询工具 + 预定义表的只读/读写操作 ✓

## File Structure
```
agenticmcp/
├── src/agenticmcp/
│   ├── __init__.py         ✓
│   ├── server.py           ✓ MCP server 主入口
│   ├── database.py         ✓ 数据库连接管理
│   ├── permissions.py      ✓ 权限控制系统
│   ├── config.py           ✓ 配置加载
│   └── tools/              ✓ MCP 工具实现
│       ├── __init__.py     ✓
│       ├── query.py        ✓ 通用查询工具
│       └── tables.py       ✓ 表操作工具
├── config/
│   └── permissions.yaml    ✓ 权限配置
├── docker/
│   ├── Dockerfile          ✓
│   ├── docker-compose.yml  ✓
│   └── init.sql            ✓ 数据库初始化脚本
├── .github/workflows/
│   ├── ci.yml              ✓ CI pipeline
│   └── release.yml         ✓ CD pipeline
├── tests/
│   ├── test_server.py      ✓
│   ├── test_database.py    ✓
│   └── test_permissions.py ✓
├── examples/
│   ├── claude_desktop_config.json ✓
│   └── inspector_config.json ✓
├── README.md               ✓ 完整文档
├── task_plan.md            ✓
└── pyproject.toml          ✓ 更新依赖
```

## Status
**✅ ALL PHASES COMPLETE** - 项目已完成，所有核心功能已实现

## Detailed Phase Breakdown

### Phase 1: 项目设计与架构
- [x] 1.1 设计整体架构
- [x] 1.2 定义权限模型
- [x] 1.3 设计 MCP 工具接口
- [x] 1.4 确定技术栈

### Phase 2: 数据库连接与模型
- [x] 2.1 实现异步 PostgreSQL 连接池
- [x] 2.2 实现数据库模型/Schema 定义
- [x] 2.3 实现查询构建器
- [x] 2.4 添加数据库连接测试

### Phase 3: MCP Server 实现
- [x] 3.1 实现通用查询工具
- [x] 3.2 实现表操作工具 (CRUD)
- [x] 3.3 实现结果格式化
- [x] 3.4 添加错误处理

### Phase 4: 权限控制系统
- [x] 4.1 实现角色定义
- [x] 4.2 实现表级权限检查
- [x] 4.3 实现列级权限过滤
- [x] 4.4 实现行级安全 (WHERE 子句注入)

### Phase 5: 配置管理
- [x] 5.1 实现 YAML 配置加载
- [x] 5.2 实现环境变量支持
- [x] 5.3 实现配置验证
- [x] 5.4 创建默认配置示例

### Phase 6: Docker 部署
- [x] 6.1 创建 Dockerfile
- [x] 6.2 创建 docker-compose.yml (含 PostgreSQL)
- [x] 6.3 创建初始化脚本
- [x] 6.4 创建健康检查

### Phase 7: GitHub Actions CI/CD
- [x] 7.1 创建 CI workflow (测试、代码检查)
- [x] 7.2 创建 Docker build workflow
- [x] 7.3 创建 release workflow
- [x] 7.4 设置版本管理

### Phase 8: 测试与文档
- [x] 8.1 添加单元测试
- [x] 8.2 添加集成测试
- [x] 8.3 添加 API 文档
- [x] 8.4 添加部署文档

### Phase 9: 示例与使用指南
- [x] 9.1 创建示例数据库 schema
- [x] 9.2 创建客户端配置示例
- [x] 9.3 编写快速开始指南
- [ ] 9.4 创建演示视频/截图 (可选)

## Deliverables

### Core Features Implemented
1. **MCP Server** (`src/agenticmcp/server.py`)
   - 8 MCP 工具 (query, list_tables, describe_table, select, insert, update, delete, get_role_info, reload_permissions)
   - 基于角色的动态工具列表

2. **数据库层** (`src/agenticmcp/database.py`)
   - 异步连接池管理
   - 安全的查询构建器 (防止 SQL 注入)
   - 表操作辅助方法

3. **权限系统** (`src/agenticmcp/permissions.py`)
   - 基于角色的访问控制 (RBAC)
   - 表级权限检查
   - 列级过滤
   - 行级安全 (WHERE 子句注入)

4. **配置管理** (`src/agenticmcp/config.py`)
   - YAML 权限配置
   - 环境变量支持
   - Pydantic 验证

5. **Docker 部署**
   - 多阶段 Dockerfile
   - Docker Compose with PostgreSQL
   - 数据库初始化脚本

6. **CI/CD Pipeline**
   - CI: Lint, Type Check, Tests
   - Release: Docker build + push to GHCR

### Files Created/Modified
| File | Status |
|------|--------|
| `src/agenticmcp/config.py` | New |
| `src/agenticmcp/database.py` | New |
| `src/agenticmcp/permissions.py` | New |
| `src/agenticmcp/server.py` | Modified |
| `src/agenticmcp/tools/__init__.py` | New |
| `src/agenticmcp/tools/query.py` | New |
| `src/agenticmcp/tools/tables.py` | New |
| `config/permissions.yaml` | New |
| `docker/Dockerfile` | New |
| `docker/docker-compose.yml` | New |
| `docker/init.sql` | New |
| `.github/workflows/ci.yml` | New |
| `.github/workflows/release.yml` | New |
| `tests/test_server.py` | Modified |
| `tests/test_database.py` | New |
| `tests/test_permissions.py` | New |
| `examples/claude_desktop_config.json` | New |
| `examples/inspector_config.json` | New |
| `README.md` | Updated |
| `pyproject.toml` | Updated |
| `task_plan.md` | New |
| `notes.md` | New |

## Next Steps / Usage

### Local Development
```bash
# Start PostgreSQL and MCP server
docker compose -f docker/docker-compose.yml up -d

# Test with inspector
npx @modelcontextprotocol/inspector
```

### Production Deployment
```bash
# Update the image reference in claude_desktop_config.json
# Push to GHCR via GitHub release tag
git tag v1.0.0
git push origin v1.0.0
```

### Custom Permissions
Edit `config/permissions.yaml` to define:
- Custom roles
- Table access lists
- Column visibility
- Row-level filters

## Errors Encountered
*None - Implementation successful!*

## Tech Stack Decisions
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| MCP Framework | `mcp` | 标准 MCP 协议库 |
| Database Driver | `asyncpg` | 高性能异步 PostgreSQL |
| Connection Pool | `asyncpg` pool | 内置连接池 |
| Configuration | `pydantic-settings` | 类型安全的配置 |
| YAML Parsing | `pyyaml` | 标准 YAML 解析 |
| Testing | `pytest` + `pytest-asyncio` | 异步测试支持 |
| Linting | `ruff` | 快速 Python linter |
| Formatting | `black` | 标准 Python 格式化 |
| Docker | Multi-stage build | 优化镜像大小 |
| CI/CD | GitHub Actions | 原生 GitHub 集成 |
