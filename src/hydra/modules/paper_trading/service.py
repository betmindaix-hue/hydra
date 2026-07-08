from hydra.modules.base import ModuleDescriptor, PipelineModule


class PaperTradingService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="paper_trading",
        purpose="Simulate orders and positions without live execution.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

