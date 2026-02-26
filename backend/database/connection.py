"""Database connection management."""

import asyncpg
from asyncpg import Pool
from typing import Optional

from backend.config import get_settings


class Database:
    """Database connection manager."""

    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls) -> Pool:
        """Create database connection pool."""
        if cls._pool is None:
            settings = get_settings()
            cls._pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                min_size=2,
                max_size=settings.db_pool_size,
            )
        return cls._pool

    @classmethod
    async def close(cls) -> None:
        """Close database connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def get_pool(cls) -> Pool:
        """Get connection pool."""
        if cls._pool is None:
            await cls.connect()
        return cls._pool

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Execute a query and return result."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args) -> list:
        """Fetch multiple rows."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(r) for r in rows]

    @classmethod
    async def fetchone(cls, query: str, *args) -> Optional[dict]:
        """Fetch a single row."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    @classmethod
    async def fetchval(cls, query: str, *args) -> any:
        """Fetch a single value."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    @classmethod
    async def transaction(cls):
        """Get a transaction context manager."""
        pool = await cls.get_pool()
        return pool.transaction()


# Convenience functions
async def execute(query: str, *args) -> str:
    """Execute a query."""
    return await Database.execute(query, *args)


async def fetch(query: str, *args) -> list:
    """Fetch multiple rows."""
    return await Database.fetch(query, *args)


async def fetchone(query: str, *args) -> Optional[dict]:
    """Fetch a single row."""
    return await Database.fetchone(query, *args)


async def fetchval(query: str, *args) -> any:
    """Fetch a single value."""
    return await Database.fetchval(query, *args)
