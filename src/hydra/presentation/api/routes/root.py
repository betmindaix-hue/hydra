from fastapi import APIRouter

from hydra.application.services import RootStatusService


def build_root_router(root_status_service: RootStatusService) -> APIRouter:
    router = APIRouter(tags=["system"])

    @router.get("/")
    def read_root() -> dict[str, object]:
        return root_status_service.execute().to_payload()

    return router

