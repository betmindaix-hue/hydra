# Observability Baseline

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

HYDRA has a minimal but production-minded observability baseline:

- JSON structured logs
- correlation IDs on request flow
- startup diagnostics with redaction rules
- `/live`, `/ready`, and `/health` endpoints
- runtime diagnostics routed through application and port boundaries

The baseline is intentionally operational, not feature-rich. Metrics, tracing, and external alerting are not yet part of scope.

## Evidence

- Logging implementation: `src/hydra/infrastructure/logging.py`
- Correlation middleware: `src/hydra/presentation/api/middleware.py`
- Runtime diagnostics adapter: `src/hydra/adapters/runtime_diagnostics.py`
- Health route assembly: `src/hydra/presentation/api/routes/health.py`
- Contract documentation: `docs/observability/Observability Baseline.md`, `docs/operations/Runtime Diagnostics Contract.md`
- Coverage and behavior tests: `tests/test_observability.py`, `tests/test_logging.py`, `tests/test_health.py`

Observed behaviors:

- request completion logs include HTTP metadata and correlation IDs
- startup diagnostics expose only approved metadata
- health surfaces distinguish process liveness from readiness and aggregate status
- live trading remains hard-disabled in diagnostics and domain blueprint output

## Commands Or Source Files Reviewed

Source files reviewed:

- `src/hydra/infrastructure/logging.py`
- `src/hydra/presentation/api/middleware.py`
- `src/hydra/adapters/runtime_diagnostics.py`
- `src/hydra/presentation/api/routes/health.py`
- `docs/observability/Observability Baseline.md`
- `docs/operations/Runtime Diagnostics Contract.md`

Supporting tests reviewed:

- `tests/test_observability.py`
- `tests/test_logging.py`
- `tests/test_health.py`

## Remaining Risks

- Readiness checks validate configuration and session wiring but not external service reachability under real operational load.
- Metrics and tracing are absent by design; future teams may overreach and add tooling before the domain model is ready.
- Observability documentation is strong now, but future feature work could accidentally expand diagnostics beyond the approved redaction contract.

## Recommendation

Keep the observability baseline stable through the first Milestone B sprint. If new offline ingestion or backtesting work is added, restrict observability changes to:

- new structured fields that remain non-sensitive
- readiness checks for newly introduced local components
- documentation updates alongside any runtime contract change
