"""FastAPI backend application."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.database.connection import Database
from backend.api.v1 import router as api_v1_router
from backend.dependencies import optional_auth_context
from backend.utils import get_audit_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Connecting to database: {settings.db_host}:{settings.db_port}/{settings.db_name}")

    try:
        await Database.connect()
        print("Database connected")

        # Initialize database schema if needed
        await init_database()

        print(f"Server ready at http://{settings.host}:{settings.port}")
    except Exception as e:
        print(f"Startup error: {e}")
        raise

    yield

    # Shutdown
    print("Shutting down...")
    await Database.close()
    print("Database closed")


async def init_database():
    """Initialize database schema."""
    from backend.database.connection import execute, fetchval

    # Create tables if they don't exist
    await execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE,
            phone TEXT,
            name TEXT NOT NULL,
            tenant_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INTEGER DEFAULT 0,
            tenant_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            status TEXT DEFAULT 'pending',
            total DECIMAL(10, 2) DEFAULT 0,
            tenant_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    """)

    await execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            tenant_id INTEGER,
            action TEXT NOT NULL,
            endpoint TEXT,
            params JSONB,
            target_id INTEGER,
            result_count INTEGER,
            status TEXT,
            error_message TEXT,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    await execute("CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_orders_tenant ON orders(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)")

    # Insert sample data if empty
    user_count = await fetchval("SELECT COUNT(*) FROM users")
    if user_count == 0:
        print("📊 Inserting sample data...")
        await insert_sample_data()


async def insert_sample_data():
    """Insert sample data for testing."""
    from backend.database.connection import execute

    # Users
    await execute("""
        INSERT INTO users (email, phone, name, tenant_id) VALUES
        ('alice@example.com', '+1234567890', 'Alice Johnson', 1),
        ('bob@example.com', '+0987654321', 'Bob Smith', 1),
        ('charlie@example.com', '+1122334455', 'Charlie Brown', 2),
        ('diana@example.com', '+5566778899', 'Diana Prince', 2)
    """)

    # Products
    await execute("""
        INSERT INTO products (name, description, price, stock, tenant_id) VALUES
        ('Laptop', 'High-performance laptop', 1299.99, 50, 1),
        ('Mouse', 'Wireless mouse', 29.99, 200, 1),
        ('Keyboard', 'Mechanical keyboard', 89.99, 100, 1),
        ('Monitor', '27-inch 4K monitor', 399.99, 75, 1),
        ('Headphones', 'Noise-cancelling headphones', 199.99, 60, 2),
        ('Webcam', 'HD webcam', 79.99, 150, 2)
    """)

    # Orders
    await execute("""
        INSERT INTO orders (user_id, status, total, tenant_id) VALUES
        (1, 'completed', 1329.98, 1),
        (1, 'pending', 89.99, 1),
        (2, 'completed', 399.99, 1),
        (3, 'shipped', 279.98, 2),
        (4, 'pending', 199.99, 2)
    """)

    print("✅ Sample data inserted")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AgenticMCP Backend API - Secure data access with JWT authentication",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(api_v1_router, prefix="/api")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "endpoints": {
                "api": "/api",
                "docs": "/docs",
                "health": "/health",
            },
        }

    # Health check
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

    # API endpoints list
    @app.get("/api")
    async def api_info():
        """Get available API endpoints."""
        return {
            "version": "v1",
            "base_url": "/api/v1",
            "endpoints": [
                {"path": "/api/v1/auth/token", "method": "POST", "description": "Create JWT token"},
                {"path": "/api/v1/auth/token/info", "method": "GET", "description": "Get token info"},
                {"path": "/api/v1/users", "methods": ["GET", "POST"], "description": "List/create users"},
                {"path": "/api/v1/users/{id}", "methods": ["GET", "PUT"], "description": "Get/update user"},
                {"path": "/api/v1/products", "methods": ["GET", "POST"], "description": "List/create products"},
                {"path": "/api/v1/products/{id}", "methods": ["GET", "PUT"], "description": "Get/update product"},
                {"path": "/api/v1/orders", "methods": ["GET", "POST"], "description": "List/create orders"},
                {"path": "/api/v1/orders/{id}", "methods": ["GET", "PATCH"], "description": "Get/update order"},
            ]
        }

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        audit = get_audit_logger()
        # Try to get user from request state if available
        user_id = getattr(request.state, "user_id", None)
        role = getattr(request.state, "role", "unknown")

        await audit.log_error(
            user_id=user_id or 0,
            role=role,
            action="server_error",
            error_message=str(exc),
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
