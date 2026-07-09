from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    app_name: str
    app_version: str
    environment: str
    api_prefix: str
    database_url: str
    redis_url: str
    log_level: str


@runtime_checkable
class RuntimeSettingsPort(Protocol):
    def load(self) -> RuntimeSettings:
        """Load runtime settings for the application."""
