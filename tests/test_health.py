from fastapi.testclient import TestClient

from hydra.main import app


client = TestClient(app)


def test_root_exposes_pipeline_and_scope() -> None:
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "HYDRA"
    assert payload["live_trading_enabled"] is False
    assert "paper_trading" in payload["pipeline"]


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

