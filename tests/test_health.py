import asyncio
from typing import Any, TypedDict

from httpx import ASGITransport, AsyncClient

from hydra.main import app


class ResponseEnvelope(TypedDict):
    status_code: int
    payload: dict[str, Any]


async def request(path: str) -> ResponseEnvelope:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(path)
    return ResponseEnvelope(
        status_code=response.status_code,
        payload=response.json(),
    )


def test_root_exposes_pipeline_and_scope() -> None:
    response = asyncio.run(request("/"))
    payload = response["payload"]

    assert response["status_code"] == 200
    assert payload["name"] == "HYDRA"
    assert payload["live_trading_enabled"] is False
    assert "paper_trading" in payload["pipeline"]


def test_health_endpoint_returns_ok() -> None:
    response = asyncio.run(request("/api/v1/health"))
    payload = response["payload"]

    assert response["status_code"] == 200
    assert payload["status"] == "ok"
