from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    app_name: str
    app_version: str
    environment: str
    api_prefix: str
    database_url: str
    redis_url: str
    log_level: str


class RuntimeSettingsPort(Protocol):
    def load(self) -> RuntimeSettings:
        """Load runtime settings for the application."""

