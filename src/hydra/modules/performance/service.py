from hydra.modules.base import ModuleDescriptor, PipelineModule


class PerformanceService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="performance",
        purpose="Produce evaluation and reporting snapshots for paper trading results.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

