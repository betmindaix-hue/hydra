from fastapi import APIRouter

from hydra.application.services import HealthStatusService, RootStatusService, SystemOverviewService
from hydra.presentation.api.routes.health import build_health_router
from hydra.presentation.api.routes.root import build_root_router
from hydra.presentation.api.routes.system import build_system_router


def build_versioned_api_router(
    health_status_service: HealthStatusService,
    system_overview_service: SystemOverviewService,
) -> APIRouter:
    router = APIRouter()
    router.include_router(build_health_router(health_status_service))
    router.include_router(build_system_router(system_overview_service))
    return router


__all__ = ["build_root_router", "build_versioned_api_router"]

