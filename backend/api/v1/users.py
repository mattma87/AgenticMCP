"""User API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from backend.dependencies import AuthDep
from backend.models.user import UserResponse, UserListResponse, UserCreate, UserUpdate
from backend.database.repositories import UserRepository
from backend.services import get_masking_service
from backend.utils import get_audit_logger

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    auth: AuthDep = None,
):
    """List users (filtered by role and tenant)."""
    user_repo = UserRepository()
    masking = get_masking_service()
    audit = get_audit_logger()

    # Apply row filter for non-admin
    tenant_id = None
    if auth.role != "admin":
        tenant_id = auth.tenant_id

    users = await user_repo.list(skip=skip, limit=limit, search=search, tenant_id=tenant_id)

    # Mask sensitive data
    masked_users = masking.mask_user_list(users, auth.role)

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="GET /api/v1/users",
        params={"skip": skip, "limit": limit, "search": search},
        result_count=len(masked_users),
    )

    return UserListResponse(users=masked_users, count=len(masked_users))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, auth: AuthDep = None):
    """Get a specific user."""
    user_repo = UserRepository()
    masking = get_masking_service()
    audit = get_audit_logger()

    # Non-admin can only view themselves
    if auth.role != "admin" and auth.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )

    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Mask sensitive data
    masked_user = masking.mask_user(user, auth.role)

    # Log access
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"GET /api/v1/users/{user_id}",
        result_count=1,
    )

    return masked_user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, auth: AuthDep = None):
    """Create a new user (admin/writer only)."""
    # Check permissions
    if auth.role not in ("admin", "writer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and writer roles can create users",
        )

    user_repo = UserRepository()
    masking = get_masking_service()
    audit = get_audit_logger()

    # Create user
    user = await user_repo.create(
        name=user_data.name,
        email=user_data.email,
        tenant_id=user_data.tenant_id,
    )

    # Mask sensitive data
    masked_user = masking.mask_user(user, auth.role)

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint="POST /api/v1/users",
        params={"name": user_data.name},
        result_count=1,
    )

    return masked_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    auth: AuthDep = None,
):
    """Update a user."""
    user_repo = UserRepository()
    masking = get_masking_service()
    audit = get_audit_logger()

    # Non-admin can only update themselves
    if auth.role != "admin" and auth.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    # Check permission for role
    if auth.role != "admin" and any(key not in ("name",) for key in user_data.model_dump(exclude_unset=True).keys()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your name",
        )

    user = await user_repo.update(
        user_id,
        name=user_data.name,
        email=user_data.email,
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Mask sensitive data
    masked_user = masking.mask_user(user, auth.role)

    # Log action
    await audit.log_access(
        user_id=auth.user_id,
        role=auth.role,
        endpoint=f"PUT /api/v1/users/{user_id}",
        result_count=1,
    )

    return masked_user
