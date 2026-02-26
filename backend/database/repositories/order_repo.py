"""Order repository."""

from typing import List, Optional
from decimal import Decimal

from backend.database.connection import fetch, fetchone, execute


class OrderRepository:
    """Order database repository."""

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        tenant_id: Optional[int] = None,
    ) -> List[dict]:
        """List orders with optional filters."""
        query = "SELECT * FROM orders WHERE 1=1"
        params = []

        if user_id is not None:
            query += " AND user_id = $1"
            params.append(user_id)

        if status is not None:
            idx = len(params) + 1
            query += f" AND status = ${idx}"
            params.append(status)

        if tenant_id is not None:
            idx = len(params) + 1
            query += f" AND tenant_id = ${idx}"
            params.append(tenant_id)

        idx = len(params) + 1
        query += f" ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, skip])

        return await fetch(query, *params)

    async def get(self, order_id: int) -> Optional[dict]:
        """Get order by ID."""
        return await fetchone("SELECT * FROM orders WHERE id = $1", order_id)

    async def create(
        self,
        user_id: int,
        status: str = "pending",
        total: Decimal = Decimal("0.00"),
        tenant_id: int = 1,
    ) -> dict:
        """Create a new order."""
        return await fetchone(
            """INSERT INTO orders (user_id, status, total, tenant_id)
            VALUES ($1, $2, $3, $4) RETURNING *""",
            user_id, status, total, tenant_id
        )

    async def update_status(self, order_id: int, status: str) -> Optional[dict]:
        """Update order status."""
        await execute(
            "UPDATE orders SET status = $1 WHERE id = $2",
            status, order_id
        )
        return await self.get(order_id)

    async def get_items(self, order_id: int) -> List[dict]:
        """Get order items."""
        return await fetch(
            """SELECT oi.*, p.name as product_name
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = $1""",
            order_id
        )
