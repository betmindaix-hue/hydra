from contextlib import asynccontextmanager

from fastapi import FastAPI

from hydra.api.router import api_router
from hydra.core.architecture import LIVE_TRADING_ENABLED, PIPELINE_STAGES
from hydra.core.config import settings
from hydra.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/", tags=["system"])
    def read_root() -> dict[str, object]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "pipeline": list(PIPELINE_STAGES),
            "live_trading_enabled": LIVE_TRADING_ENABLED,
            "docs_source": "docs/",
        }

    return app


app = create_app()

