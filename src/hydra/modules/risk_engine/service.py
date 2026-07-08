from hydra.modules.base import ModuleDescriptor, PipelineModule


class RiskEngineService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="risk_engine",
        purpose="Apply safety checks and sizing before paper trades are simulated.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

