# ADR-0005: Add a Deterministic Fixture Strategy Research Provider

Date: 2026-07-18
Status: Accepted

## Context

HYDRA already has:

- B1 offline market data primitives and series modeling
- B3 offline backtesting request and `ResearchSignal` language
- B4 application-level strategy research orchestration through
  `StrategyResearchProviderPort`

The next safe step is to introduce a concrete provider implementation that can
exercise the B4 boundary without adding price-derived strategy behavior,
external IO, persistence, or execution concepts.

Milestone B still requires:

- offline-first, deterministic behavior
- no framework leakage into domain rules
- no runtime coupling from research into infrastructure or presentation
- no trading, routing, or broker-facing behavior

HYDRA needs a laboratory-grade provider that can produce explicit
`ResearchSignal` objects from a static fixture plan so downstream B3 handoff
and future research workflows can be validated with deterministic inputs.

## Decision

Add an adapter-level deterministic fixture provider:

- `src/hydra/adapters/strategy_research/__init__.py`
- `src/hydra/adapters/strategy_research/deterministic_fixture_provider.py`

The new adapter introduces:

- `FixtureSignalInstruction`
- `DeterministicFixtureStrategyResearchProvider`

The provider implements `StrategyResearchProviderPort` by mapping explicit
fixture instructions to bars selected from a `StrategyResearchRequest`. It
emits `ResearchSignal` objects only from instruction metadata and selected bar
timestamps.

The provider remains:

- deterministic
- synchronous
- in-memory
- fixture-driven
- offline-first

No price-pattern inspection, indicator logic, optimization, or production
strategy behavior is added in this ADR.

## Affected Layers

- `adapters/`: deterministic fixture provider implementation
- `tests/`: provider unit coverage and adapter guardrails
- `docs/`: ADR, research note, and review package

No new domain models, infrastructure adapters, API endpoints, persistence, or
runtime services are introduced.

## Diagram

```mermaid
flowchart LR
    Series["B1 MarketDataSeries"] --> Request["B4 StrategyResearchRequest"]
    Request --> Provider["B5 DeterministicFixtureStrategyResearchProvider"]
    Provider --> Signals["B3 ResearchSignal tuple"]
    Signals --> Result["B4 StrategyResearchResult"]
    Result -. explicit handoff .-> Backtest["B3 BacktestRequest"]
```

## Alternatives Considered

### Put fixture generation directly inside the B4 application service

Rejected because it would mix orchestration with provider-specific fixture
logic and weaken the port boundary introduced in B4.

### Add a filesystem-backed provider first

Rejected because B5 is meant to stay purely in-memory and deterministic. File
access would add unnecessary adapter surface area and IO coupling.

### Add price-derived research behavior now

Rejected because B5 is a fixture provider, not a strategy engine. Price
analysis, indicators, and optimization remain outside Milestone B scope.

## Consequences

### Positive

- B4 now has a concrete offline provider for deterministic integration tests
- B3 handoff can be exercised without adding strategy logic
- future offline providers can follow a proven adapter boundary

### Negative

- the provider is intentionally limited and cannot express dynamic research
  behavior
- another adapter adds a small amount of package structure

### Neutral

- no infrastructure wiring changes are required
- no runtime configuration changes are required
- no external behavior changes occur outside the new research fixture path

## Rollback Strategy

If the fixture adapter becomes too narrow or confusing, revert the provider,
tests, and documentation together in one PR. Because the adapter is local,
stateless, and free of persistence or network behavior, rollback remains low
risk and does not require migration.

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
- no ML models
- no automatic trading
- no production strategy implementation
- no indicator engine
- no moving-average strategy
- no RSI strategy
