from hydra.application.dto import (
    HealthStatusDTO,
    OperationalStatusDTO,
    RootStatusDTO,
    SystemOverviewDTO,
)
from hydra.domain.system import HYDRA_SYSTEM_BLUEPRINT, module_summary_map
from hydra.ports.observability import RuntimeCheck, RuntimeDiagnosticsPort
from hydra.ports.runtime_settings import RuntimeSettingsPort


class RootStatusService:
    def __init__(self, settings_port: RuntimeSettingsPort):
        self._settings_port = settings_port

    def execute(self) -> RootStatusDTO:
        runtime_settings = self._settings_port.load()
        blueprint = HYDRA_SYSTEM_BLUEPRINT
        return RootStatusDTO(
            name=runtime_settings.app_name,
            version=runtime_settings.app_version,
            environment=runtime_settings.environment,
            pipeline=blueprint.pipeline_stages,
            live_trading_enabled=blueprint.live_trading_enabled,
            docs_source=blueprint.docs_source,
        )


class HealthStatusService:
    def __init__(
        self,
        settings_port: RuntimeSettingsPort,
        diagnostics_port: RuntimeDiagnosticsPort,
    ):
        self._settings_port = settings_port
        self._diagnostics_port = diagnostics_port

    def execute(self) -> HealthStatusDTO:
        runtime_settings = self._settings_port.load()
        checks = _checks_as_payload(self._diagnostics_port.readiness_checks())
        return HealthStatusDTO(
            status=_overall_status(checks),
            app_name=runtime_settings.app_name,
            app_version=runtime_settings.app_version,
            environment=runtime_settings.environment,
            checks=checks,
        )


class LivenessStatusService:
    def __init__(self, settings_port: RuntimeSettingsPort):
        self._settings_port = settings_port

    def execute(self) -> OperationalStatusDTO:
        runtime_settings = self._settings_port.load()
        return OperationalStatusDTO(
            status="ok",
            app_name=runtime_settings.app_name,
            app_version=runtime_settings.app_version,
            environment=runtime_settings.environment,
            checks={"process": "ok"},
        )


class ReadinessStatusService:
    def __init__(
        self,
        settings_port: RuntimeSettingsPort,
        diagnostics_port: RuntimeDiagnosticsPort,
    ):
        self._settings_port = settings_port
        self._diagnostics_port = diagnostics_port

    def execute(self) -> OperationalStatusDTO:
        runtime_settings = self._settings_port.load()
        checks = _checks_as_payload(self._diagnostics_port.readiness_checks())
        return OperationalStatusDTO(
            status=_overall_status(checks),
            app_name=runtime_settings.app_name,
            app_version=runtime_settings.app_version,
            environment=runtime_settings.environment,
            checks=checks,
        )


class SystemOverviewService:
    def execute(self) -> SystemOverviewDTO:
        blueprint = HYDRA_SYSTEM_BLUEPRINT
        return SystemOverviewDTO(
            pipeline=blueprint.pipeline_stages,
            core_entities=blueprint.core_entities,
            non_goals=blueprint.non_goals,
            modules=module_summary_map(blueprint),
        )


def _checks_as_payload(checks: tuple[RuntimeCheck, ...]) -> dict[str, str]:
    return {check.name: check.status for check in checks}


def _overall_status(checks: dict[str, str]) -> str:
    return "ok" if all(status == "ok" for status in checks.values()) else "error"
