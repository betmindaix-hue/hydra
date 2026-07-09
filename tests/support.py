from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from httpx import ASGITransport, AsyncClient

from hydra.ports.runtime_settings import RuntimeSettings


class StaticSettingsPort:
    def __init__(self, settings: RuntimeSettings) -> None:
        self._settings = settings
        self.load_calls = 0

    def load(self) -> RuntimeSettings:
        self.load_calls += 1
        return self._settings


class ResponseEnvelope(TypedDict):
    status_code: int
    payload: dict[str, Any]
    headers: dict[str, str]


def build_runtime_settings(
    *,
    database_url: str = "sqlite+pysqlite:///:memory:",
    environment: str = "test",
    log_level: str = "INFO",
    api_prefix: str = "/api/v1",
) -> RuntimeSettings:
    return RuntimeSettings(
        app_name="HYDRA",
        app_version="0.1.0",
        environment=environment,
        api_prefix=api_prefix,
        database_url=database_url,
        redis_url="redis://localhost:6379/0",
        log_level=log_level,
    )


async def request(
    app: Any,
    path: str,
    *,
    headers: Mapping[str, str] | None = None,
) -> ResponseEnvelope:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(path, headers=headers)

    return ResponseEnvelope(
        status_code=response.status_code,
        payload=response.json(),
        headers=dict(response.headers),
    )
