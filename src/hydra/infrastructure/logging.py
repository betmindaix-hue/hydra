import json
import logging
from datetime import UTC, datetime
from typing import TextIO

from hydra.ports.runtime_settings import RuntimeSettings
from hydra.shared.correlation import get_correlation_id

OPTIONAL_LOG_FIELDS = (
    "correlation_id",
    "http_method",
    "http_path",
    "status_code",
    "duration_ms",
    "api_prefix",
    "live_trading_enabled",
    "architecture_mode",
    "database_backend",
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": getattr(record, "environment", "unknown"),
            "app_name": getattr(record, "app_name", "unknown"),
            "app_version": getattr(record, "app_version", "unknown"),
        }

        for field_name in OPTIONAL_LOG_FIELDS:
            field_value = getattr(record, field_name, None)
            if field_value is not None:
                payload[field_name] = field_value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, separators=(",", ":"))


class RuntimeContextFilter(logging.Filter):
    def __init__(self, settings: RuntimeSettings) -> None:
        super().__init__()
        self._settings = settings

    def filter(self, record: logging.LogRecord) -> bool:
        record.environment = self._settings.environment
        record.app_name = self._settings.app_name
        record.app_version = self._settings.app_version

        correlation_id = get_correlation_id()
        if correlation_id is not None:
            record.correlation_id = correlation_id

        return True


def resolve_log_level(log_level: str) -> int:
    return getattr(logging, log_level.upper(), logging.INFO)


def configure_logging(settings: RuntimeSettings, stream: TextIO | None = None) -> None:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(RuntimeContextFilter(settings))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(resolve_log_level(settings.log_level))
    root_logger.addHandler(handler)


def get_database_backend(database_url: str) -> str:
    return database_url.partition(":")[0] or "unknown"


def build_startup_diagnostics(
    settings: RuntimeSettings,
    *,
    live_trading_enabled: bool,
    architecture_mode: str,
) -> dict[str, object]:
    return {
        "api_prefix": settings.api_prefix,
        "live_trading_enabled": live_trading_enabled,
        "architecture_mode": architecture_mode,
        "database_backend": get_database_backend(settings.database_url),
    }


def log_startup_diagnostics(
    settings: RuntimeSettings,
    *,
    live_trading_enabled: bool,
    architecture_mode: str,
) -> None:
    logging.getLogger("hydra.startup").info(
        "application startup diagnostics",
        extra=build_startup_diagnostics(
            settings,
            live_trading_enabled=live_trading_enabled,
            architecture_mode=architecture_mode,
        ),
    )
