# Next Phase Recommendation

Date: 2026-07-17
Scope: HYDRA Engineering Task A8
Recommended next milestone: Milestone B - Research Data Foundation

## Current State

Milestone A established the repository baseline needed to start carefully expanding the product model. The next phase should add only research-safe and offline-first capabilities. Infrastructure should continue to follow the existing architectural contract rather than introducing a second architecture.

## Evidence

- DDD plus Hexagonal Architecture is established and enforced.
- Quality, security, configuration, observability, operations, and workstation baselines are in place.
- Live trading and exchange execution are still out of scope in both code and documentation.

## Commands Or Source Files Reviewed

Source files reviewed:

- `docs/adr/ADR-0001-hexagonal-architecture.md`
- `docs/engineering/Engineering Standards.md`
- `docs/configuration/Environment Strategy.md`
- `docs/reviews/a1_1_cleanup_review.md` through `docs/reviews/a7_developer_workstation_review.md`

## Guardrails

Milestone B must preserve:

- no live trading
- no exchange execution
- no exchange API keys
- no real-money operations
- offline-first
- test-first
- ports-before-adapters
- domain model before infrastructure
- architecture tests updated before new adapters

## Sprint Options

### B1: Market Data Domain Model

Focus:

- define exchange-agnostic market data concepts in `domain/`
- add related DTOs and application contracts
- do not add live collectors or exchange adapters

### B2: Offline Dataset Ingestion

Focus:

- add offline dataset import ports and use-case scaffolding
- support local file-based or fixture-driven ingestion only
- do not add background workers or live polling

### B3: Backtesting Skeleton

Focus:

- define pure-Python backtesting contracts and orchestration seams
- keep execution simulated and fully offline
- do not add broker, exchange, or wallet concepts

## Remaining Risks

- Milestone B can fail if it starts with adapters instead of domain and ports.
- Teams may treat future-oriented blueprint names as permission to add live-facing behavior.
- Branch protection should be enabled before work volume increases.

## Recommendation

Start with B1 if the goal is domain clarity, B2 if the goal is data flow scaffolding, or B3 if the goal is research execution structure. Among these, B1 is the safest first sprint because it strengthens the model before new infrastructure is introduced.
