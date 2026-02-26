#!/usr/bin/env python3
"""Database initialization script for AgenticMCP."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def init_database():
    """Initialize database schema."""
    from backend.config import get_settings
    from backend.database.connection import Database, execute, fetchval

    settings = get_settings()

    print("=" * 60)
    print("AgenticMCP Database Initialization")
    print("=" * 60)
    print(f"Host:     {settings.db_host}:{settings.db_port}")
    print(f"Database: {settings.db_name}")
    print(f"User:     {settings.db_user}")
    print()

    # First, connect to 'postgres' database to create target database if needed
    print("Creating database if needed...")
    try:
        # Connect to postgres default database
        import asyncpg
        conn = await asyncpg.connect(
            host=settings.db_host,
            port=settings.db_port,
            database="postgres",
            user=settings.db_user,
            password=settings.db_password,
        )

        # Check if agenticmcp exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.db_name
        )

        if not db_exists:
            await conn.execute(f'CREATE DATABASE "{settings.db_name}"')
            print(f"  [OK] Database '{settings.db_name}' created")
        else:
            print(f"  [OK] Database '{settings.db_name}' already exists")

        await conn.close()
    except Exception as e:
        print(f"  [ERROR] Failed to create database: {e}")
        return False

    # Now connect to the target database
    print()
    print("Connecting to PostgreSQL...")
    try:
        await Database.connect()
        print("  [OK] Connected")
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        print()
        print("Tips:")
        print("   - Make sure PostgreSQL is running")
        print("   - Check your connection settings")
        print(f"   - User: {settings.db_user}, Password: {'***' if settings.db_password else '(not set)'}")
        return False

    # Create tables
    print()
    print("Creating tables...")

    # Users table
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
    print("  [OK] users")

    # Products table
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
    print("  [OK] products")

    # Orders table
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
    print("  [OK] orders")

    # Order items table
    await execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    """)
    print("  [OK] order_items")

    # Audit logs table
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
    print("  [OK] audit_logs")

    # Create indexes
    print()
    print("Creating indexes...")
    await execute("CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_orders_tenant ON orders(tenant_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)")
    await execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)")
    print("  [OK] Indexes created")

    # Check if sample data needed
    user_count = await fetchval("SELECT COUNT(*) FROM users")
    if user_count == 0:
        print()
        print("Inserting sample data...")

        # Users
        await execute("""
            INSERT INTO users (email, phone, name, tenant_id) VALUES
            ('alice@example.com', '+1234567890', 'Alice Johnson', 1),
            ('bob@example.com', '+0987654321', 'Bob Smith', 1),
            ('charlie@example.com', '+1122334455', 'Charlie Brown', 2),
            ('diana@example.com', '+5566778899', 'Diana Prince', 2)
        """)
        print("  [OK] 4 users")

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
        print("  [OK] 6 products")

        # Orders
        await execute("""
            INSERT INTO orders (user_id, status, total, tenant_id) VALUES
            (1, 'completed', 1329.98, 1),
            (1, 'pending', 89.99, 1),
            (2, 'completed', 399.99, 1),
            (3, 'shipped', 279.98, 2),
            (4, 'pending', 199.99, 2)
        """)
        print("  [OK] 5 orders")
    else:
        print()
        print(f"Sample data already exists ({user_count} users)")

    # Close connection
    await Database.close()

    print()
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(init_database())
