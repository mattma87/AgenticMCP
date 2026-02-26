"""User repository."""

from typing import List, Optional
from datetime import datetime

from backend.database.connection import fetch, fetchone, execute


class UserRepository:
    """User database repository."""

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        tenant_id: Optional[int] = None,
    ) -> List[dict]:
        """List users with optional filters."""
        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if search:
            query += " AND name ILIKE $1"
            params.append(f"%{search}%")

        if tenant_id is not None:
            if not search:
                query += " AND tenant_id = $1"
                params.append(tenant_id)
            else:
                query += " AND tenant_id = $2"
                params.append(tenant_id)

        query += " ORDER BY id LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
        params.extend([limit, skip])

        return await fetch(query, *params)

    async def get(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        return await fetchone("SELECT * FROM users WHERE id = $1", user_id)

    async def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        return await fetchone("SELECT * FROM users WHERE email = $1", email)

    async def create(self, name: str, email: Optional[str], tenant_id: int = 1) -> dict:
        """Create a new user."""
        result = await execute(
            "INSERT INTO users (name, email, tenant_id) VALUES ($1, $2, $3) RETURNING *",
            name, email, tenant_id
        )
        return await fetchone("SELECT * FROM users WHERE id = (SELECT lastval())")

    async def update(self, user_id: int, name: Optional[str] = None, email: Optional[str] = None) -> Optional[dict]:
        """Update user."""
        updates = []
        params = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if email is not None:
            updates.append(f"email = ${param_idx}")
            params.append(email)
            param_idx += 1

        if not updates:
            return await self.get(user_id)

        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1

        params.append(user_id)

        await execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ${param_idx}",
            *params
        )

        return await self.get(user_id)

    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        result = await execute("DELETE FROM users WHERE id = $1", user_id)
        return "DELETE 1" in result

    async def count(self, tenant_id: Optional[int] = None) -> int:
        """Count users."""
        if tenant_id is not None:
            return await fetchval("SELECT COUNT(*) FROM users WHERE tenant_id = $1", tenant_id)
        return await fetchval("SELECT COUNT(*) FROM users")
