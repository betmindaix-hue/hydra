from hydra.application.dto import HealthStatusDTO, RootStatusDTO, SystemOverviewDTO
from hydra.domain.system import HYDRA_SYSTEM_BLUEPRINT, module_summary_map
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
    def execute(self) -> HealthStatusDTO:
        return HealthStatusDTO(
            status="ok",
            live_trading_enabled=HYDRA_SYSTEM_BLUEPRINT.live_trading_enabled,
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
