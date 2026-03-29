from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.catalog import router as catalog_router
from app.api.v1.endpoints.consumer import router as consumer_router
from app.api.v1.endpoints.franchise import router as franchise_router
from app.api.v1.endpoints.orders import client_router as client_orders_router
from app.api.v1.endpoints.orders import router as orders_router
from app.api.v1.endpoints.preorders import router as preorders_router
from app.api.v1.endpoints.production import router as production_router
from app.api.v1.endpoints.sizes import router as sizes_router
from app.api.v1.endpoints.try_on import router as try_on_router
from app.api.v1.endpoints.wardrobes import router as wardrobes_router

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(ai_router)
router.include_router(catalog_router)
router.include_router(consumer_router)
router.include_router(sizes_router)
router.include_router(try_on_router)
router.include_router(wardrobes_router)
router.include_router(client_orders_router)
router.include_router(preorders_router)
router.include_router(franchise_router)
router.include_router(orders_router)
router.include_router(production_router)
