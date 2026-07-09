import asyncio
from typing import Any, TypedDict

from hydra.main import create_app
from tests.support import StaticSettingsPort, build_runtime_settings, request


class ResponseEnvelope(TypedDict):
    status_code: int
    payload: dict[str, Any]


def build_test_app():
    return create_app(settings_port=StaticSettingsPort(build_runtime_settings()))


def test_root_exposes_pipeline_and_scope() -> None:
    response = asyncio.run(request(build_test_app(), "/"))
    payload = response["payload"]

    assert response["status_code"] == 200
    assert payload["name"] == "HYDRA"
    assert payload["live_trading_enabled"] is False
    assert "paper_trading" in payload["pipeline"]


def test_health_endpoint_returns_ok() -> None:
    response = asyncio.run(request(build_test_app(), "/api/v1/health"))
    payload = response["payload"]

    assert response["status_code"] == 200
    assert payload["status"] == "ok"
    assert payload["checks"]["configuration"] == "ok"
    assert payload["checks"]["database_session"] == "ok"
