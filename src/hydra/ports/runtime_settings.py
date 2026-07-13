from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hydra.shared.runtime_environment import RuntimeEnvironment


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    app_name: str
    app_version: str
    environment: RuntimeEnvironment
    api_prefix: str
    database_url: str
    redis_url: str
    log_level: str


@runtime_checkable
class RuntimeSettingsPort(Protocol):
    def load(self) -> RuntimeSettings:
        """Load runtime settings for the application."""
