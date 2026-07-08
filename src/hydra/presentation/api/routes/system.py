from fastapi import APIRouter

from hydra.application.services import SystemOverviewService


def build_system_router(system_overview_service: SystemOverviewService) -> APIRouter:
    router = APIRouter(prefix="/system", tags=["system"])

    @router.get("/overview")
    def read_system_overview() -> dict[str, object]:
        return system_overview_service.execute().to_payload()

    return router

