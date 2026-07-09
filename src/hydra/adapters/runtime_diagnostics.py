from collections.abc import Callable

from hydra.adapters.runtime_settings import PydanticRuntimeSettingsAdapter
from hydra.infrastructure.database.session import build_session_factory
from hydra.ports.observability import RuntimeCheck, RuntimeDiagnosticsPort
from hydra.ports.runtime_settings import RuntimeSettingsPort


class RuntimeDiagnosticsAdapter(RuntimeDiagnosticsPort):
    def __init__(self, settings_port: RuntimeSettingsPort | None = None):
        self._settings_port = settings_port or PydanticRuntimeSettingsAdapter()

    def readiness_checks(self) -> tuple[RuntimeCheck, ...]:
        return (
            self._run_check("configuration", self._load_settings),
            self._run_check("database_session", self._validate_database_session),
        )

    def _load_settings(self) -> None:
        self._settings_port.load()

    def _validate_database_session(self) -> None:
        session_factory = build_session_factory(self._settings_port)
        session = session_factory()
        session.close()

    @staticmethod
    def _run_check(name: str, operation: Callable[[], None]) -> RuntimeCheck:
        try:
            operation()
        except Exception:
            return RuntimeCheck(name=name, status="error")
        return RuntimeCheck(name=name, status="ok")
