from __future__ import annotations

import asyncio
import json
from io import StringIO

from hydra.infrastructure.logging import (
    build_startup_diagnostics,
    configure_logging,
)
from hydra.main import create_app
from hydra.shared.correlation import reset_correlation_id, set_correlation_id
from tests.support import StaticSettingsPort, build_runtime_settings


def test_configure_logging_emits_valid_json_with_expected_fields() -> None:
    stream = StringIO()
    settings = build_runtime_settings()

    configure_logging(settings, stream=stream)

    token = set_correlation_id("corr-123")
    try:
        import logging

        logging.getLogger("hydra.test").info("structured log works")
    finally:
        reset_correlation_id(token)

    payload = json.loads(stream.getvalue().strip())

    assert payload["message"] == "structured log works"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "hydra.test"
    assert payload["environment"] == "test"
    assert payload["app_name"] == "HYDRA"
    assert payload["app_version"] == "0.1.0"
    assert payload["correlation_id"] == "corr-123"
    assert "timestamp" in payload


def test_log_level_is_configurable() -> None:
    stream = StringIO()
    settings = build_runtime_settings(log_level="WARNING")

    configure_logging(settings, stream=stream)

    import logging

    logger = logging.getLogger("hydra.test.level")
    logger.info("this should be filtered")
    logger.warning("this should be emitted")

    lines = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]

    assert len(lines) == 1
    assert lines[0]["level"] == "WARNING"
    assert lines[0]["message"] == "this should be emitted"


def test_startup_diagnostics_do_not_leak_database_secrets() -> None:
    settings = build_runtime_settings(
        database_url="postgresql+psycopg://hydra:supersecret@localhost:5432/hydra"
    )

    diagnostics = build_startup_diagnostics(
        settings,
        live_trading_enabled=False,
        architecture_mode="ddd-hexagonal",
    )

    assert diagnostics["database_backend"] == "postgresql+psycopg"
    assert "supersecret" not in json.dumps(diagnostics)


def test_app_startup_logs_structured_diagnostics() -> None:
    stream = StringIO()
    settings_port = StaticSettingsPort(
        build_runtime_settings(
            database_url="postgresql+psycopg://hydra:supersecret@localhost:5432/hydra"
        )
    )
    app = create_app(settings_port=settings_port, log_stream=stream)

    async def run_lifespan() -> None:
        async with app.router.lifespan_context(app):
            return None

    asyncio.run(run_lifespan())

    log_lines = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    startup_log = next(
        line for line in log_lines if line["message"] == "application startup diagnostics"
    )

    assert startup_log["api_prefix"] == "/api/v1"
    assert startup_log["live_trading_enabled"] is False
    assert startup_log["architecture_mode"] == "ddd-hexagonal"
    assert startup_log["database_backend"] == "postgresql+psycopg"
    assert "supersecret" not in stream.getvalue()
