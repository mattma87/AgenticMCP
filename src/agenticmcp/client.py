"""HTTP client for calling the AgenticMCP API."""

import json
import os
from typing import Any, Optional
from urllib.parse import urlencode

import httpx


class APIClient:
    """Client for making HTTP requests to the AgenticMCP backend API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API (default: from MCP_API_URL env var)
            token: JWT token for authentication (default: from MCP_JWT_TOKEN env var)
        """
        self.base_url = base_url or os.getenv(
            "MCP_API_URL",
            "http://localhost:8000"
        )
        self.token = token or os.getenv("MCP_JWT_TOKEN", "")

        if not self.token:
            raise ValueError(
                "MCP_JWT_TOKEN environment variable must be set. "
                "Generate a token using: agenticmcp-token --user-id 1 --role reader"
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., /api/v1/users)
            params: Query parameters
            json_data: JSON body data

        Returns:
            Response data as dict
        """
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(
                        url,
                        headers=self.headers,
                        params=params,
                    )
                elif method == "POST":
                    response = await client.post(
                        url,
                        headers=self.headers,
                        params=params,
                        json=json_data,
                    )
                elif method == "PUT":
                    response = await client.put(
                        url,
                        headers=self.headers,
                        json=json_data,
                    )
                elif method == "PATCH":
                    response = await client.patch(
                        url,
                        headers=self.headers,
                        json=json_data,
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        url,
                        headers=self.headers,
                    )
                else:
                    return {"success": False, "error": f"Unknown method: {method}"}

                # Try to parse JSON response
                try:
                    data = response.json()
                except ValueError:
                    data = {"response": response.text}

                # Check for errors
                if response.status_code >= 400:
                    return {
                        "success": False,
                        "error": data.get("error") or data.get("detail"),
                        "status_code": response.status_code,
                    }

                return {"success": True, "data": data, "status_code": response.status_code}

            except httpx.ConnectError:
                return {
                    "success": False,
                    "error": f"Cannot connect to API at {self.base_url}. "
                           "Make sure the backend server is running."
                }
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "error": "Request timed out",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }

    async def get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_data: dict) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", path, json_data=json_data)

    async def put(self, path: str, json_data: dict) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", path, json_data=json_data)

    async def patch(self, path: str, json_data: dict) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", path, json_data=json_data)

    async def delete(self, path: str) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", path)

    async def get_endpoints(self) -> dict[str, Any]:
        """Get list of available API endpoints."""
        return await self.get("/api")

    async def get_token_info(self) -> dict[str, Any]:
        """Get information about the current token."""
        return await self.get("/api/v1/auth/token/info")

    # User endpoints
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> dict[str, Any]:
        """List users."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        return await self.get("/api/v1/users", params)

    async def get_user(self, user_id: int) -> dict[str, Any]:
        """Get a specific user."""
        return await self.get(f"/api/v1/users/{user_id}")

    async def create_user(
        self,
        name: str,
        email: Optional[str] = None,
        tenant_id: int = 1,
    ) -> dict[str, Any]:
        """Create a new user."""
        return await self.post("/api/v1/users", {
            "name": name,
            "email": email,
            "tenant_id": tenant_id,
        })

    async def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update a user."""
        data = {}
        if name is not None:
            data["name"] = name
        if email is not None:
            data["email"] = email
        return await self.put(f"/api/v1/users/{user_id}", data)

    # Product endpoints
    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: bool = False,
    ) -> dict[str, Any]:
        """List products."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if in_stock:
            params["in_stock"] = "true"
        return await self.get("/api/v1/products", params)

    async def get_product(self, product_id: int) -> dict[str, Any]:
        """Get a specific product."""
        return await self.get(f"/api/v1/products/{product_id}")

    async def create_product(
        self,
        name: str,
        price: float,
        stock: int = 0,
        description: Optional[str] = None,
        tenant_id: int = 1,
    ) -> dict[str, Any]:
        """Create a new product."""
        return await self.post("/api/v1/products", {
            "name": name,
            "price": price,
            "stock": stock,
            "description": description,
            "tenant_id": tenant_id,
        })

    async def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        stock: Optional[int] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update a product."""
        data = {}
        if name is not None:
            data["name"] = name
        if price is not None:
            data["price"] = price
        if stock is not None:
            data["stock"] = stock
        if description is not None:
            data["description"] = description
        return await self.put(f"/api/v1/products/{product_id}", data)

    # Order endpoints
    async def list_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """List orders."""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return await self.get("/api/v1/orders", params)

    async def get_order(self, order_id: int) -> dict[str, Any]:
        """Get a specific order."""
        return await self.get(f"/api/v1/orders/{order_id}")

    async def create_order(
        self,
        user_id: int,
        status: str = "pending",
        tenant_id: int = 1,
    ) -> dict[str, Any]:
        """Create a new order."""
        return await self.post("/api/v1/orders", {
            "user_id": user_id,
            "status": status,
            "tenant_id": tenant_id,
        })

    async def update_order_status(
        self,
        order_id: int,
        status: str,
    ) -> dict[str, Any]:
        """Update order status."""
        # Note: This uses a different path pattern
        return await self._request("PATCH", f"/api/v1/orders/{order_id}/status", json_data={"new_status": status})


# Global client instance
_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get global API client instance."""
    global _client
    if _client is None:
        _client = APIClient()
    return _client
