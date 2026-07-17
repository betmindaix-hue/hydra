# Architecture Baseline

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

HYDRA currently conforms to the accepted DDD plus Hexagonal Architecture baseline:

- `domain/` is pure Python and framework-free
- `application/` depends on `domain` and `ports`
- `presentation/` exposes FastAPI routes and middleware but does not access the ORM directly
- `adapters/` implement runtime-facing ports
- `infrastructure/` owns configuration, logging, and database primitives
- `main.py` acts as the composition root

The architecture is intentionally small, but the dependency direction is explicit and automated.

## Evidence

- ADR source: `docs/adr/ADR-0001-hexagonal-architecture.md`
- Composition root: `src/hydra/main.py`
- Application orchestration: `src/hydra/application/services.py`
- Domain blueprint: `src/hydra/domain/system.py`
- Port contracts: `src/hydra/ports/runtime_settings.py`, `src/hydra/ports/observability.py`
- Adapter implementations: `src/hydra/adapters/runtime_settings.py`, `src/hydra/adapters/runtime_diagnostics.py`
- Architecture enforcement: `tests/test_architecture_layers.py`

Observed baseline characteristics:

- Domain purity rules remain intact.
- Runtime configuration is kept outside the application layer.
- Presentation routes rely on application services rather than direct infrastructure calls.
- Architecture rules are codified in tests rather than documentation alone.

## Commands Or Source Files Reviewed

Source files reviewed:

- `src/hydra/main.py`
- `src/hydra/application/services.py`
- `src/hydra/domain/system.py`
- `src/hydra/presentation/api/middleware.py`
- `src/hydra/adapters/runtime_diagnostics.py`
- `tests/test_architecture_layers.py`

Supporting review documents:

- `docs/reviews/architecture_review_v1.md`
- `docs/reviews/refactor_report.md`

## Remaining Risks

- The domain blueprint still names future product modules such as market collection and paper trading; those are documented as future concepts, but they can attract premature implementation if governance weakens.
- The repository has only a small set of ports today; future persistence and ingestion work could bypass the intended direction if repository ports are added casually.
- Architecture tests cover dependency direction well, but they do not yet validate every possible future adapter category.

## Recommendation

Treat the current architecture as the Milestone A contract:

- add new domain concepts before infrastructure implementations
- introduce repository ports only when a concrete application use case requires them
- expand architecture fitness tests before new adapters are merged
- avoid introducing alternative architectural styles during Milestone B unless a new ADR justifies the change
