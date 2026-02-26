"""Product repository."""

from typing import List, Optional
from decimal import Decimal

from backend.database.connection import fetch, fetchone, execute, fetchval


class ProductRepository:
    """Product database repository."""

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock: bool = False,
        tenant_id: Optional[int] = None,
    ) -> List[dict]:
        """List products with optional filters."""
        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if search:
            query += " AND (name ILIKE $1 OR description ILIKE $1)"
            params.append(f"%{search}%")

        if min_price is not None:
            idx = len(params) + 1
            query += f" AND price >= ${idx}"
            params.append(min_price)

        if max_price is not None:
            idx = len(params) + 1
            query += f" AND price <= ${idx}"
            params.append(max_price)

        if in_stock:
            idx = len(params) + 1
            query += f" AND stock > ${idx}"
            params.append(0)

        if tenant_id is not None:
            idx = len(params) + 1
            query += f" AND tenant_id = ${idx}"
            params.append(tenant_id)

        idx = len(params) + 1
        query += f" ORDER BY id LIMIT ${idx} OFFSET ${idx + 1}"
        params.extend([limit, skip])

        return await fetch(query, *params)

    async def get(self, product_id: int) -> Optional[dict]:
        """Get product by ID."""
        return await fetchone("SELECT * FROM products WHERE id = $1", product_id)

    async def create(
        self,
        name: str,
        price: Decimal,
        stock: int = 0,
        description: Optional[str] = None,
        tenant_id: int = 1,
    ) -> dict:
        """Create a new product."""
        return await fetchone(
            """INSERT INTO products (name, price, stock, description, tenant_id)
            VALUES ($1, $2, $3, $4, $5) RETURNING *""",
            name, price, stock, description, tenant_id
        )

    async def update(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        stock: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """Update product."""
        updates = []
        params = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if price is not None:
            updates.append(f"price = ${param_idx}")
            params.append(price)
            param_idx += 1

        if stock is not None:
            updates.append(f"stock = ${param_idx}")
            params.append(stock)
            param_idx += 1

        if description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(description)
            param_idx += 1

        if not updates:
            return await self.get(product_id)

        params.append(product_id)

        await execute(
            f"UPDATE products SET {', '.join(updates)} WHERE id = ${param_idx}",
            *params
        )

        return await self.get(product_id)

    async def delete(self, product_id: int) -> bool:
        """Delete product."""
        result = await execute("DELETE FROM products WHERE id = $1", product_id)
        return "DELETE 1" in result
