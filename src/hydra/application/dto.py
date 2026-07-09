from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RootStatusDTO:
    name: str
    version: str
    environment: str
    pipeline: tuple[str, ...]
    live_trading_enabled: bool
    docs_source: str

    def to_payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "environment": self.environment,
            "pipeline": list(self.pipeline),
            "live_trading_enabled": self.live_trading_enabled,
            "docs_source": self.docs_source,
        }


@dataclass(frozen=True, slots=True)
class HealthStatusDTO:
    status: str
    app_name: str
    app_version: str
    environment: str
    checks: dict[str, str]

    def to_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "checks": dict(self.checks),
        }


@dataclass(frozen=True, slots=True)
class SystemOverviewDTO:
    pipeline: tuple[str, ...]
    core_entities: tuple[str, ...]
    non_goals: tuple[str, ...]
    modules: dict[str, str]

    def to_payload(self) -> dict[str, object]:
        return {
            "pipeline": list(self.pipeline),
            "core_entities": list(self.core_entities),
            "non_goals": list(self.non_goals),
            "modules": dict(self.modules),
        }


@dataclass(frozen=True, slots=True)
class OperationalStatusDTO:
    status: str
    app_name: str
    app_version: str
    environment: str
    checks: dict[str, str]

    def to_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "checks": dict(self.checks),
        }
