"""Database connection and query management."""

import asyncio
from datetime import datetime
from typing import Any

import asyncpg
from asyncpg import Pool

from .config import get_settings


class DatabaseManager:
    """Manage database connections and queries."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self._pool: Pool | None = None
        self._lock = asyncio.Lock()

    async def get_pool(self) -> Pool:
        """Get or create the connection pool."""
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    settings = get_settings()
                    self._pool = await asyncpg.create_pool(
                        host=settings.db_host,
                        port=settings.db_port,
                        database=settings.db_name,
                        user=settings.db_user,
                        password=settings.db_password,
                        min_size=settings.db_pool_min_size,
                        max_size=settings.db_pool_size,
                        command_timeout=settings.query_timeout,
                    )
        return self._pool

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def execute_query(
        self,
        query: str,
        params: list[Any] | None = None,
        fetch: str = "all",
    ) -> list[dict[str, Any]] | str:
        """
        Execute a database query.

        Args:
            query: SQL query with placeholders ($1, $2, etc.)
            params: Query parameters
            fetch: 'all', 'one', or 'none' (for INSERT/UPDATE/DELETE)

        Returns:
            Query results as list of dicts or status message
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            if fetch == "all":
                rows = await conn.fetch(query, *(params or []))
                return [dict(row) for row in rows]
            elif fetch == "one":
                row = await conn.fetchrow(query, *(params or []))
                return dict(row) if row is not None else {}
            else:
                result = await conn.execute(query, *(params or []))
                return result

    async def list_tables(self) -> list[str]:
        """List all tables in the database."""
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """
        rows = await self.execute_query(query)
        return [row["tablename"] for row in rows]

    async def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        """Get table schema information."""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = $1
            ORDER BY ordinal_position
        """
        return await self.execute_query(query, [table_name])

    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM pg_tables
                WHERE schemaname = 'public' AND tablename = $1
            )
        """
        result = await self.execute_query(query, [table_name], fetch="one")
        return result.get("exists", False)

    def sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize a SQL identifier (table or column name).

        Only allows alphanumeric characters and underscores.
        """
        if not identifier.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid identifier: {identifier}")
        return f'"{identifier}"'

    def build_select_query(
        self,
        table: str,
        columns: list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[str, list[Any]]:
        """
        Build a SELECT query with safe parameter binding.

        Returns:
            Tuple of (query, params)
        """
        safe_table = self.sanitize_identifier(table)

        if columns:
            safe_columns = ", ".join(self.sanitize_identifier(c) for c in columns)
        else:
            safe_columns = "*"

        query = f"SELECT {safe_columns} FROM {safe_table}"
        params: list[Any] = []

        if where:
            conditions = []
            for i, (key, value) in enumerate(where.items(), 1):
                safe_col = self.sanitize_identifier(key)
                conditions.append(f"{safe_col} = ${i}")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)

        if order_by:
            safe_order = self.sanitize_identifier(order_by)
            query += f" ORDER BY {safe_order}"

        if limit:
            params.append(offset)
            params.append(limit)
            query += f" OFFSET ${len(params)-1} LIMIT ${len(params)}"

        return query, params

    def build_insert_query(
        self,
        table: str,
        data: dict[str, Any],
        returning: str | None = None,
    ) -> tuple[str, list[Any]]:
        """
        Build an INSERT query with safe parameter binding.

        Returns:
            Tuple of (query, params)
        """
        safe_table = self.sanitize_identifier(table)

        columns = list(data.keys())
        safe_columns = ", ".join(self.sanitize_identifier(c) for c in columns)
        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        params = list(data.values())

        query = f"INSERT INTO {safe_table} ({safe_columns}) VALUES ({placeholders})"

        if returning:
            safe_returning = self.sanitize_identifier(returning)
            query += f" RETURNING {safe_returning}"

        return query, params

    def build_update_query(
        self,
        table: str,
        data: dict[str, Any],
        where: dict[str, Any],
        returning: str | None = None,
    ) -> tuple[str, list[Any]]:
        """
        Build an UPDATE query with safe parameter binding.

        Returns:
            Tuple of (query, params)
        """
        safe_table = self.sanitize_identifier(table)

        set_parts = []
        params: list[Any] = []
        param_idx = 1

        for key, value in data.items():
            safe_col = self.sanitize_identifier(key)
            set_parts.append(f"{safe_col} = ${param_idx}")
            params.append(value)
            param_idx += 1

        query = f"UPDATE {safe_table} SET {', '.join(set_parts)}"

        conditions = []
        for key, value in where.items():
            safe_col = self.sanitize_identifier(key)
            conditions.append(f"{safe_col} = ${param_idx}")
            params.append(value)
            param_idx += 1

        query += " WHERE " + " AND ".join(conditions)

        if returning:
            safe_returning = self.sanitize_identifier(returning)
            query += f" RETURNING {safe_returning}"

        return query, params

    def build_delete_query(
        self,
        table: str,
        where: dict[str, Any],
        returning: str | None = None,
    ) -> tuple[str, list[Any]]:
        """
        Build a DELETE query with safe parameter binding.

        Returns:
            Tuple of (query, params)
        """
        safe_table = self.sanitize_identifier(table)

        query = f"DELETE FROM {safe_table}"
        params: list[Any] = []
        param_idx = 1

        conditions = []
        for key, value in where.items():
            safe_col = self.sanitize_identifier(key)
            conditions.append(f"{safe_col} = ${param_idx}")
            params.append(value)
            param_idx += 1

        query += " WHERE " + " AND ".join(conditions)

        if returning:
            safe_returning = self.sanitize_identifier(returning)
            query += f" RETURNING {safe_returning}"

        return query, params

    async def get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a table."""
        schema = await self.describe_table(table_name)
        return [col["column_name"] for col in schema]


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def close_db() -> None:
    """Close the database connection pool."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None
