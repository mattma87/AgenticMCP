"""Product API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from decimal import Decimal

from backend.dependencies import AuthDep
from backend.models.product import ProductResponse, ProductListResponse, ProductCreate, ProductUpdate
from backend.database.repositories import ProductRepository
from backend.utils import get_audit_logger

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock: bool = False,
    auth: AuthDep = None,
):
    """List products with optional filters."""
    product_repo = ProductRepository()
    audit = get_audit_logger()

    # Apply tenant filter for non-admin
    tenant_id = None
    if auth.role != "admin":
        tenant_id = auth.tenant_id

    products = await product_repo.list(
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        tenant_id=tenant_id,
    )

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="GET /api/v1/products",
        params={
            "skip": skip,
            "limit": limit,
            "search": search,
            "min_price": str(min_price) if min_price else None,
            "max_price": str(max_price) if max_price else None,
            "in_stock": in_stock,
        },
        result_count=len(products),
    )

    return ProductListResponse(products=products, count=len(products))


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, auth: AuthDep = None):
    """Get a specific product."""
    product_repo = ProductRepository()
    audit = get_audit_logger()

    product = await product_repo.get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Check tenant access
    if auth.role != "admin" and product.get("tenant_id") != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"GET /api/v1/products/{product_id}",
        result_count=1,
    )

    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, auth: AuthDep = None):
    """Create a new product (admin/writer only)."""
    if auth.role not in ("admin", "writer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and writer roles can create products",
        )

    product_repo = ProductRepository()
    audit = get_audit_logger()

    product = await product_repo.create(
        name=product_data.name,
        price=product_data.price,
        stock=product_data.stock,
        description=product_data.description,
        tenant_id=product_data.tenant_id,
    )

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="POST /api/v1/products",
        params={"name": product_data.name, "price": str(product_data.price)},
        result_count=1,
    )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    auth: AuthDep = None,
):
    """Update a product (admin/writer only)."""
    if auth.role not in ("admin", "writer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and writer roles can update products",
        )

    product_repo = ProductRepository()
    audit = get_audit_logger()

    product = await product_repo.get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Check tenant access
    if auth.role != "admin" and product.get("tenant_id") != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Update
    product = await product_repo.update(
        product_id,
        name=product_data.name,
        price=product_data.price,
        stock=product_data.stock,
        description=product_data.description,
    )

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"PUT /api/v1/products/{product_id}",
        result_count=1,
    )

    return product
