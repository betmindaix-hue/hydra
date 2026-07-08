from hydra.modules.base import ModuleDescriptor, PipelineModule


class DecisionEngineService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="decision_engine",
        purpose="Explain and persist decisions derived from strategy signals.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

