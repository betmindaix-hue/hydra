from fastapi import APIRouter

from hydra.application.services import (
    HealthStatusService,
    LivenessStatusService,
    ReadinessStatusService,
)


def build_operations_router(
    health_status_service: HealthStatusService,
    liveness_status_service: LivenessStatusService,
    readiness_status_service: ReadinessStatusService,
) -> APIRouter:
    router = APIRouter(tags=["operations"])

    @router.get("/health")
    def read_health() -> dict[str, object]:
        return health_status_service.execute().to_payload()

    @router.get("/live")
    def read_liveness() -> dict[str, object]:
        return liveness_status_service.execute().to_payload()

    @router.get("/ready")
    def read_readiness() -> dict[str, object]:
        return readiness_status_service.execute().to_payload()

    return router
