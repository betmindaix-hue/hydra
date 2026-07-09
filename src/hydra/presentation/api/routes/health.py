from fastapi import APIRouter

from hydra.application.services import HealthStatusService


def build_health_router(health_status_service: HealthStatusService) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("")
    def read_health() -> dict[str, object]:
        return health_status_service.execute().to_payload()

    return router
