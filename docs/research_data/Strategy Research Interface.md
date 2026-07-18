# Strategy Research Interface

Date: 2026-07-18
Scope: HYDRA Engineering Task B4

## Purpose

B4 introduces HYDRA's first offline strategy research interface. Its purpose is
to request and validate research signals from a trusted offline research
provider without adding live strategies, broker execution, infrastructure
adapters, or automatic trading behavior.

## Offline Strategy Research Boundary

What B4 does:

- accepts a validated `MarketDataSeries`
- accepts a research id, optional time bounds, and optional primitive parameters
- calls a strategy research provider through a port
- validates generated `ResearchSignal` timestamps against the selected dataset
- reports duplicate or out-of-range signals explicitly
- optionally hands valid signals forward to B3 as a `BacktestRequest`

What B4 does not do:

- execute trades
- place or route orders
- connect to exchanges or brokers
- read production files
- write to a database
- expose API endpoints
- run background jobs or schedulers

## B1, B2, and B3 Alignment

B4 stays downstream of the existing boundaries.

Reused B1 concepts:

- `Symbol`
- `Market`
- `Timeframe`
- `OHLCVBar`
- `MarketDataSeries`
- `DataSourceDescriptor`

Reused B2 flow assumptions:

- offline ingestion is already complete before strategy research starts
- B4 does not parse raw records or load datasets directly

Reused B3 concepts:

- `ResearchSignal`
- `BacktestDirection`
- `BacktestRequest`

## Port Responsibility

`src/hydra/ports/strategy_research.py` defines:

- `StrategyResearchProviderPort`

The port only describes offline signal generation. It does not implement:

- filesystem access
- CSV, parquet, or JSON readers
- database repositories
- exchange clients
- broker clients
- live market connectivity

## Application Service Responsibility

`src/hydra/application/strategy_research_dto.py` defines:

- `StrategyResearchRequest`
- `StrategyResearchError`
- `StrategyResearchResult`

`src/hydra/application/strategy_research_service.py` provides
`OfflineStrategyResearchService`.

The service:

- validates request boundaries and parameters
- resolves the effective research window
- invokes the provider synchronously
- validates timestamps against the selected series
- rejects duplicate signals per timestamp
- returns an explicit result object
- never runs a backtest unless a caller explicitly requests the B3 handoff

## Diagram

```mermaid
flowchart LR
    Series["B1 MarketDataSeries"] --> Request["StrategyResearchRequest"]
    Request --> Service["OfflineStrategyResearchService"]
    Service --> Port["StrategyResearchProviderPort"]
    Port --> Signals["ResearchSignal tuple"]
    Signals --> Result["StrategyResearchResult"]
    Result -. explicit handoff only .-> B3["B3 BacktestRequest"]
    B2["B2 Offline Ingestion"] -. prepares series earlier .-> Series
```

## Future Extension Path

Future milestones may add offline research providers for:

- deterministic rule-based research experiments
- fixture-backed research evaluation
- reporting or comparison tooling layered on top of research results

Those providers must remain outside the current port and application boundary
unless a later milestone explicitly approves a broader design.

## Explicitly Not Implemented

- production moving-average strategies
- RSI or indicator engines
- ML models
- AI strategy generation
- exchange-aware strategies
- live signal dispatch
- automatic backtest execution

## Non-Goals

- live trading
- paper trading
- Binance integration
- exchange adapters
- broker adapters
- exchange execution
- order routing
- wallet logic
- API keys
- WebSocket
- live market data collection
- database persistence
- API endpoints
- background workers
- AI strategy generation
- ML models
- automatic trading
