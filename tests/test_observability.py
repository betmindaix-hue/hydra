from __future__ import annotations

import asyncio
import json
from io import StringIO
from uuid import UUID

from fastapi import FastAPI

from hydra.main import create_app
from hydra.ports.observability import RuntimeCheck, RuntimeDiagnosticsPort
from tests.support import StaticSettingsPort, build_runtime_settings, request


class StableDiagnosticsPort(RuntimeDiagnosticsPort):
    def readiness_checks(self) -> tuple[RuntimeCheck, ...]:
        return (
            RuntimeCheck(name="configuration", status="ok"),
            RuntimeCheck(name="database_session", status="ok"),
        )


class ExplodingDiagnosticsPort(RuntimeDiagnosticsPort):
    def readiness_checks(self) -> tuple[RuntimeCheck, ...]:
        raise AssertionError("live endpoint must not request readiness checks")


class FailingDiagnosticsPort(RuntimeDiagnosticsPort):
    def readiness_checks(self) -> tuple[RuntimeCheck, ...]:
        return (
            RuntimeCheck(name="configuration", status="ok"),
            RuntimeCheck(name="database_session", status="error"),
        )


def build_app(
    *,
    diagnostics_port: RuntimeDiagnosticsPort | None = None,
    stream: StringIO | None = None,
) -> FastAPI:
    settings_port = StaticSettingsPort(build_runtime_settings())
    return create_app(
        settings_port=settings_port,
        diagnostics_port=diagnostics_port or StableDiagnosticsPort(),
        log_stream=stream,
    )


def test_live_endpoint_returns_process_liveness_without_readiness_dependencies() -> None:
    app = build_app(diagnostics_port=ExplodingDiagnosticsPort())

    response = asyncio.run(request(app, "/live"))

    assert response["status_code"] == 200
    assert response["payload"] == {
        "status": "ok",
        "app_name": "HYDRA",
        "app_version": "0.1.0",
        "environment": "test",
        "checks": {"process": "ok"},
    }


def test_ready_endpoint_returns_structured_dependency_checks() -> None:
    app = build_app()

    response = asyncio.run(request(app, "/ready"))

    assert response["status_code"] == 200
    assert response["payload"] == {
        "status": "ok",
        "app_name": "HYDRA",
        "app_version": "0.1.0",
        "environment": "test",
        "checks": {
            "configuration": "ok",
            "database_session": "ok",
        },
    }


def test_health_endpoint_returns_aggregate_status_and_metadata() -> None:
    app = build_app()

    response = asyncio.run(request(app, "/health"))

    assert response["status_code"] == 200
    assert response["payload"] == {
        "status": "ok",
        "app_name": "HYDRA",
        "app_version": "0.1.0",
        "environment": "test",
        "checks": {
            "configuration": "ok",
            "database_session": "ok",
        },
    }


def test_ready_endpoint_returns_error_when_a_readiness_check_fails() -> None:
    app = build_app(diagnostics_port=FailingDiagnosticsPort())

    response = asyncio.run(request(app, "/ready"))

    assert response["status_code"] == 200
    assert response["payload"]["status"] == "error"
    assert response["payload"]["checks"]["configuration"] == "ok"
    assert response["payload"]["checks"]["database_session"] == "error"


def test_health_endpoint_returns_error_when_aggregate_readiness_fails() -> None:
    app = build_app(diagnostics_port=FailingDiagnosticsPort())

    response = asyncio.run(request(app, "/health"))

    assert response["status_code"] == 200
    assert response["payload"]["status"] == "error"
    assert response["payload"]["checks"]["configuration"] == "ok"
    assert response["payload"]["checks"]["database_session"] == "error"


def test_versioned_health_endpoint_retains_observability_payload() -> None:
    app = build_app()

    response = asyncio.run(request(app, "/api/v1/health"))

    assert response["status_code"] == 200
    assert response["payload"]["checks"]["configuration"] == "ok"
    assert response["payload"]["checks"]["database_session"] == "ok"


def test_incoming_correlation_id_is_preserved_and_returned_in_response_headers() -> None:
    stream = StringIO()
    app = build_app(stream=stream)

    response = asyncio.run(
        request(app, "/health", headers={"X-Correlation-ID": "corr-incoming-123"})
    )

    assert response["headers"]["x-correlation-id"] == "corr-incoming-123"

    log_lines = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    request_log = next(line for line in log_lines if line["message"] == "request completed")

    assert request_log["correlation_id"] == "corr-incoming-123"


def test_missing_correlation_id_is_generated_and_returned_in_response_headers() -> None:
    app = build_app()

    response = asyncio.run(request(app, "/live"))

    generated_correlation_id = response["headers"]["x-correlation-id"]

    assert generated_correlation_id
    assert str(UUID(generated_correlation_id)) == generated_correlation_id
