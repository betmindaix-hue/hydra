from hydra.modules.base import ModuleDescriptor, PipelineModule


class MemoryService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="memory",
        purpose="Persist patterns and experiments for reproducible research.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

