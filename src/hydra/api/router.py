from fastapi import APIRouter

from hydra.api.routes.health import router as health_router
from hydra.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(system_router)

