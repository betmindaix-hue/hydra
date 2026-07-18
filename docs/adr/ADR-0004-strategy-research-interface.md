# ADR-0004: Add a Strategy Research Interface

Date: 2026-07-18
Status: Accepted

## Context

HYDRA now has an offline market data language from B1, an offline ingestion
boundary from B2, and an offline backtesting skeleton from B3. The next safe
step is to introduce an application-facing research boundary that can generate
`ResearchSignal` objects from a validated `MarketDataSeries` without adding
live strategies, exchange execution, infrastructure adapters, or external IO.

The repository already enforces:

- DDD plus Hexagonal Architecture dependency direction
- offline-first, in-memory research workflows
- no live trading or exchange execution in Milestone B
- architecture fitness tests that block framework leakage and risky keywords

HYDRA needs a clean way to request offline research signals so future research
providers can plug in without contaminating domain, backtesting, or
infrastructure layers.

## Decision

Add a strategy research interface composed of:

- `src/hydra/ports/strategy_research.py`
- `src/hydra/application/strategy_research_dto.py`
- `src/hydra/application/strategy_research_service.py`

The new boundary introduces:

- `StrategyResearchProviderPort`
- `StrategyResearchRequest`
- `StrategyResearchError`
- `StrategyResearchResult`
- `OfflineStrategyResearchService`

This interface remains deterministic, synchronous, local, and offline-first.
It accepts a validated `MarketDataSeries`, resolves an effective research time
range, asks a provider for `ResearchSignal` objects, validates those signals,
and optionally hands them forward to B3 through `BacktestRequest`.

No production strategy implementation is added in this ADR.

## Affected Layers

- `ports/`: new strategy research provider interface
- `application/`: new DTOs, orchestration, validation, and optional B3 handoff
- `tests/`: unit coverage and architecture safety checks
- `docs/`: ADR, research-data guide, and review package

No `domain/`, `adapters/`, `infrastructure/`, or `presentation/` runtime
implementation is added beyond reuse of existing B1 and B3 concepts.

## Diagram

```mermaid
flowchart LR
    Series["B1 MarketDataSeries"] --> Request["StrategyResearchRequest"]
    Request --> Service["OfflineStrategyResearchService"]
    Service --> Port["StrategyResearchProviderPort"]
    Port --> Signals["ResearchSignal tuple"]
    Signals --> Result["StrategyResearchResult"]
    Result -. optional handoff .-> Backtest["B3 BacktestRequest"]
```

## Alternatives Considered

### Put research generation directly inside the backtesting service

Rejected because it would mix signal production concerns with simulation logic
and blur the B3 boundary.

### Add concrete offline strategies now

Rejected because B4 is meant to create the interface only, not production
research implementations.

### Add infrastructure-backed provider implementations first

Rejected because it would pull filesystem, database, or service concerns into a
boundary that should stay pure and testable.

## Consequences

### Positive

- future offline research providers have a clear plug-in boundary
- B3 continues to consume `ResearchSignal` objects without owning signal generation
- request validation, signal validation, and backtest handoff stay explicit and testable

### Negative

- another application boundary adds a bit more orchestration structure
- real research logic is still intentionally absent, so only test and future
  provider implementations can exercise the port

### Neutral

- no live behavior changes
- no framework wiring changes
- no new runtime infrastructure dependencies

## Rollback Strategy

If the interface proves too narrow or awkward, revert the new port, DTOs,
service, tests, and documentation together in one PR. Because no persistence,
networking, or API behavior is introduced, rollback remains low risk and does
not require data migration.

## Explicit Non-Goals

- no live trading
- no paper trading
- no exchange integration
- no Binance integration
- no broker integration
- no API keys
- no WebSocket
- no external network calls
- no real order execution
- no wallet logic
- no database persistence
- no API endpoints
- no AI strategy generation
- no automatic trading
