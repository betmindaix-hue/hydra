from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RuntimeCheck:
    name: str
    status: str


@runtime_checkable
class RuntimeDiagnosticsPort(Protocol):
    def readiness_checks(self) -> tuple[RuntimeCheck, ...]:
        """Collect readiness checks for runtime dependencies."""
