from hydra.modules.base import ModuleDescriptor, PipelineModule


class StrategyEngineService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="strategy_engine",
        purpose="Transform feature sets into versioned strategy signals.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

