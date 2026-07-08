from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModuleDefinition:
    name: str
    purpose: str


@dataclass(frozen=True, slots=True)
class HydraSystemBlueprint:
    pipeline_stages: tuple[str, ...]
    core_entities: tuple[str, ...]
    non_goals: tuple[str, ...]
    modules: tuple[ModuleDefinition, ...]
    live_trading_enabled: bool = False
    docs_source: str = "docs/"


HYDRA_SYSTEM_BLUEPRINT = HydraSystemBlueprint(
    pipeline_stages=(
        "market_collector",
        "feature_engine",
        "strategy_engine",
        "decision_engine",
        "risk_engine",
        "paper_trading",
        "performance",
        "memory",
    ),
    core_entities=(
        "MarketBar",
        "FeatureSet",
        "StrategySignal",
        "Decision",
        "PaperTrade",
        "PerformanceSnapshot",
        "Pattern",
        "Experiment",
    ),
    non_goals=(
        "high-frequency trading",
        "multi-user SaaS",
        "live execution in v1",
    ),
    modules=(
        ModuleDefinition(
            name="market_collector",
            purpose="Collects market data and preserves raw exchange payloads.",
        ),
        ModuleDefinition(
            name="feature_engine",
            purpose="Builds repeatable technical and derived features from market bars.",
        ),
        ModuleDefinition(
            name="strategy_engine",
            purpose="Transforms features into versioned strategy signals.",
        ),
        ModuleDefinition(
            name="decision_engine",
            purpose="Explains and records candidate actions from strategy signals.",
        ),
        ModuleDefinition(
            name="risk_engine",
            purpose="Applies safety checks and sizing before any paper trade is created.",
        ),
        ModuleDefinition(
            name="paper_trading",
            purpose="Simulates orders and positions without live execution.",
        ),
        ModuleDefinition(
            name="performance",
            purpose="Tracks outcome metrics, drawdowns and evaluation snapshots.",
        ),
        ModuleDefinition(
            name="memory",
            purpose="Stores reusable patterns and experiment lineage for reproducible research.",
        ),
    ),
)


def module_summary_map(blueprint: HydraSystemBlueprint = HYDRA_SYSTEM_BLUEPRINT) -> dict[str, str]:
    return {module.name: module.purpose for module in blueprint.modules}

