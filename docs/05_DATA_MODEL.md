# Data Model

Core entities:
- MarketBar
- FeatureSet
- StrategySignal
- Decision
- PaperTrade
- PerformanceSnapshot
- Pattern
- Experiment

Relationships:
MarketBar -> FeatureSet -> StrategySignal -> Decision -> PaperTrade
