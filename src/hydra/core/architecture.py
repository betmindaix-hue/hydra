PIPELINE_STAGES = (
    "market_collector",
    "feature_engine",
    "strategy_engine",
    "decision_engine",
    "risk_engine",
    "paper_trading",
    "performance",
    "memory",
)

CORE_ENTITIES = (
    "MarketBar",
    "FeatureSet",
    "StrategySignal",
    "Decision",
    "PaperTrade",
    "PerformanceSnapshot",
    "Pattern",
    "Experiment",
)

NON_GOALS = (
    "high-frequency trading",
    "multi-user SaaS",
    "live execution in v1",
)

MODULE_SUMMARIES = {
    "market_collector": "Collects market data and preserves raw exchange payloads.",
    "feature_engine": "Builds repeatable technical and derived features from market bars.",
    "strategy_engine": "Transforms features into versioned strategy signals.",
    "decision_engine": "Explains and records candidate actions from strategy signals.",
    "risk_engine": "Applies safety checks and sizing before any paper trade is created.",
    "paper_trading": "Simulates orders and positions without live execution.",
    "performance": "Tracks outcome metrics, drawdowns and evaluation snapshots.",
    "memory": "Stores reusable patterns and experiment lineage for reproducible research.",
}

LIVE_TRADING_ENABLED = False

