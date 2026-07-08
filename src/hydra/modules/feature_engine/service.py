from hydra.modules.base import ModuleDescriptor, PipelineModule


class FeatureEngineService(PipelineModule):
    descriptor = ModuleDescriptor(
        name="feature_engine",
        purpose="Compute repeatable technical features from raw market bars.",
    )

    def run(self) -> None:
        raise NotImplementedError("Defined by a future SDS package.")

