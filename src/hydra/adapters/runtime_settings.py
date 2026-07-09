from hydra.infrastructure.config import Settings, get_settings
from hydra.ports.runtime_settings import RuntimeSettings, RuntimeSettingsPort


class PydanticRuntimeSettingsAdapter(RuntimeSettingsPort):
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def load(self) -> RuntimeSettings:
        settings = self._settings
        return RuntimeSettings(
            app_name=settings.app_name,
            app_version=settings.app_version,
            environment=settings.environment,
            api_prefix=settings.api_prefix,
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            log_level=settings.log_level,
        )
