from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TextIO

from fastapi import FastAPI

from hydra.adapters.runtime_diagnostics import RuntimeDiagnosticsAdapter
from hydra.adapters.runtime_settings import PydanticRuntimeSettingsAdapter
from hydra.application.services import (
    HealthStatusService,
    LivenessStatusService,
    ReadinessStatusService,
    RootStatusService,
    SystemOverviewService,
)
from hydra.domain.system import HYDRA_SYSTEM_BLUEPRINT
from hydra.infrastructure.logging import configure_logging, log_startup_diagnostics
from hydra.ports.observability import RuntimeDiagnosticsPort
from hydra.ports.runtime_settings import RuntimeSettingsPort
from hydra.presentation.api.middleware import CorrelationIdMiddleware
from hydra.presentation.api.router import (
    build_operations_router,
    build_root_router,
    build_versioned_api_router,
)

ARCHITECTURE_MODE = "ddd-hexagonal"


def create_app(
    settings_port: RuntimeSettingsPort | None = None,
    diagnostics_port: RuntimeDiagnosticsPort | None = None,
    log_stream: TextIO | None = None,
) -> FastAPI:
    runtime_settings_port = settings_port or PydanticRuntimeSettingsAdapter()
    runtime_settings = runtime_settings_port.load()
    runtime_diagnostics_port = diagnostics_port or RuntimeDiagnosticsAdapter(runtime_settings_port)

    root_status_service = RootStatusService(runtime_settings_port)
    health_status_service = HealthStatusService(runtime_settings_port, runtime_diagnostics_port)
    liveness_status_service = LivenessStatusService(runtime_settings_port)
    readiness_status_service = ReadinessStatusService(
        runtime_settings_port,
        runtime_diagnostics_port,
    )
    system_overview_service = SystemOverviewService()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging(runtime_settings, stream=log_stream)
        log_startup_diagnostics(
            runtime_settings,
            live_trading_enabled=HYDRA_SYSTEM_BLUEPRINT.live_trading_enabled,
            architecture_mode=ARCHITECTURE_MODE,
        )
        yield

    app = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(build_root_router(root_status_service))
    app.include_router(
        build_operations_router(
            health_status_service=health_status_service,
            liveness_status_service=liveness_status_service,
            readiness_status_service=readiness_status_service,
        )
    )
    app.include_router(
        build_versioned_api_router(
            health_status_service=health_status_service,
            system_overview_service=system_overview_service,
        ),
        prefix=runtime_settings.api_prefix,
    )
    return app


app = create_app()
