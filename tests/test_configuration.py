from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from hydra.infrastructure.config import Settings
from hydra.main import create_app
from hydra.shared.runtime_environment import RuntimeEnvironment
from tests.support import StaticSettingsPort, build_runtime_settings, request

VALID_DATABASE_URL = "postgresql+psycopg://placeholder:placeholder@localhost:5432/hydra_local"
VALID_REDIS_URL = "redis://localhost:6379/0"


def build_settings(**overrides: object) -> Settings:
    payload: dict[str, object] = {
        "app_name": "HYDRA",
        "app_version": "0.1.0",
        "environment": RuntimeEnvironment.LOCAL,
        "api_prefix": "/api/v1",
        "database_url": VALID_DATABASE_URL,
        "redis_url": VALID_REDIS_URL,
        "log_level": "INFO",
    }
    payload.update(overrides)
    return Settings.model_validate(payload)


def test_default_settings_use_supported_runtime_contract() -> None:
    settings = Settings.model_validate({})

    assert settings.app_name == "HYDRA"
    assert settings.app_version == "0.1.0"
    assert settings.environment is RuntimeEnvironment.LOCAL
    assert settings.api_prefix == "/api/v1"
    assert settings.database_url == VALID_DATABASE_URL
    assert settings.redis_url == VALID_REDIS_URL
    assert settings.log_level == "INFO"


@pytest.mark.parametrize("environment", list(RuntimeEnvironment))
def test_settings_accept_supported_environment_values(
    environment: RuntimeEnvironment,
) -> None:
    settings = build_settings(environment=environment)

    assert settings.environment is environment


def test_settings_reject_invalid_environment_values() -> None:
    with pytest.raises(ValidationError):
        build_settings(environment="production")


@pytest.mark.parametrize("api_prefix", ("api/v1", "/api/v1/"))
def test_settings_reject_invalid_api_prefixes(api_prefix: str) -> None:
    with pytest.raises(ValidationError):
        build_settings(api_prefix=api_prefix)


def test_settings_accept_root_api_prefix() -> None:
    settings = build_settings(api_prefix="/")

    assert settings.api_prefix == "/"


def test_settings_reject_invalid_log_levels() -> None:
    with pytest.raises(ValidationError):
        build_settings(log_level="TRACE")


def test_settings_requires_database_url() -> None:
    with pytest.raises(ValidationError):
        build_settings(database_url="  ")


def test_settings_requires_redis_url() -> None:
    with pytest.raises(ValidationError):
        build_settings(redis_url="")


def test_production_like_environment_keeps_live_trading_disabled() -> None:
    app = create_app(
        settings_port=StaticSettingsPort(
            build_runtime_settings(environment=RuntimeEnvironment.PRODUCTION_LIKE)
        )
    )

    response = asyncio.run(request(app, "/"))

    assert response["status_code"] == 200
    assert response["payload"]["environment"] == "production-like"
    assert response["payload"]["live_trading_enabled"] is False
