"""Order API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from backend.dependencies import AuthDep
from backend.models.order import OrderResponse, OrderListResponse, OrderCreate
from backend.database.repositories import OrderRepository
from backend.utils import get_audit_logger

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=OrderListResponse)
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    auth: AuthDep = None,
):
    """List orders (filtered by role and tenant)."""
    order_repo = OrderRepository()
    audit = get_audit_logger()

    # Apply row filter for non-admin
    user_id = None
    tenant_id = None

    if auth.role != "admin":
        user_id = auth.user_id
        tenant_id = auth.tenant_id

    orders = await order_repo.list(
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status_filter,
        tenant_id=tenant_id,
    )

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="GET /api/v1/orders",
        params={"skip": skip, "limit": limit, "status": status_filter},
        result_count=len(orders),
    )

    return OrderListResponse(orders=orders, count=len(orders))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, auth: AuthDep = None):
    """Get a specific order."""
    order_repo = OrderRepository()
    audit = get_audit_logger()

    order = await order_repo.get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Check access
    if auth.role != "admin" and order.get("user_id") != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"GET /api/v1/orders/{order_id}",
        result_count=1,
    )

    return order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, auth: AuthDep = None):
    """Create a new order."""
    order_repo = OrderRepository()
    audit = get_audit_logger()

    # Non-admin can only create orders for themselves
    if auth.role != "admin" and order_data.user_id != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create orders for yourself",
        )

    # Create order
    order = await order_repo.create(
        user_id=order_data.user_id,
        status=order_data.status,
        tenant_id=order_data.tenant_id,
    )

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="POST /api/v1/orders",
        params={"user_id": order_data.user_id, "status": order_data.status},
        result_count=1,
    )

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    new_status: str,
    auth: AuthDep = None,
):
    """Update order status (admin/writer only)."""
    if auth.role not in ("admin", "writer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and writer roles can update order status",
        )

    order_repo = OrderRepository()
    audit = get_audit_logger()

    order = await order_repo.get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Check tenant access
    if auth.role != "admin" and order.get("tenant_id") != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    order = await order_repo.update_status(order_id, new_status)

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"PATCH /api/v1/orders/{order_id}/status",
        params={"status": new_status},
        result_count=1,
    )

    return order
