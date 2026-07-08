from contextlib import asynccontextmanager

from fastapi import FastAPI

from hydra.adapters.runtime_settings import PydanticRuntimeSettingsAdapter
from hydra.application.services import HealthStatusService, RootStatusService, SystemOverviewService
from hydra.infrastructure.logging import configure_logging
from hydra.ports.runtime_settings import RuntimeSettingsPort
from hydra.presentation.api.router import build_root_router, build_versioned_api_router


def create_app(settings_port: RuntimeSettingsPort | None = None) -> FastAPI:
    runtime_settings_port = settings_port or PydanticRuntimeSettingsAdapter()
    runtime_settings = runtime_settings_port.load()

    root_status_service = RootStatusService(runtime_settings_port)
    health_status_service = HealthStatusService()
    system_overview_service = SystemOverviewService()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        configure_logging(runtime_settings.log_level)
        yield

    app = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(build_root_router(root_status_service))
    app.include_router(
        build_versioned_api_router(
            health_status_service=health_status_service,
            system_overview_service=system_overview_service,
        ),
        prefix=runtime_settings.api_prefix,
    )
    return app


app = create_app()

