"""API v1 router."""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .products import router as products_router
from .orders import router as orders_router

router = APIRouter(prefix="/v1")

# Include all sub-routers (they already have their own prefixes)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(products_router)
router.include_router(orders_router)
