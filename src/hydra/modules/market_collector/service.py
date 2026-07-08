from hydra.modules.base import ModuleDescriptor, PipelineModule


class MarketCollectorService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="market_collector",
        purpose="Collect market data and preserve raw exchange payloads.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

