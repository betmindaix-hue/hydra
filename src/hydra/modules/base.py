from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDescriptor:
    name: str
    purpose: str


class PipelineModule(ABC):
    descriptor: ModuleDescriptor

    @abstractmethod
    def run(self) -> None:
        """Execute the module's primary workflow."""

