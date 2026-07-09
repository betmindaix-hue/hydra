# Observability Baseline

Date: 2026-07-09
Scope: HYDRA Engineering Task A2

## Purpose

HYDRA's first observability baseline establishes production-grade visibility without adding business behavior. The baseline covers:

- structured JSON logging
- request correlation IDs
- startup diagnostics
- operational health endpoints
- reviewable operational documentation

## Architectural Placement

- `infrastructure/logging.py` owns logging configuration and JSON formatting
- `presentation/api/middleware.py` owns HTTP correlation ID handling and request logging
- `adapters/runtime_diagnostics.py` owns readiness checks for configuration and database session wiring
- `application/services.py` owns operational status DTO assembly
- `shared/correlation.py` provides framework-agnostic request correlation context

## Baseline Capabilities

1. Every application log is emitted as machine-readable JSON.
2. Every HTTP response carries `X-Correlation-ID`.
3. Request logs include the request correlation ID.
4. Startup logs include sanitized runtime diagnostics.
5. `/health`, `/live`, and `/ready` expose structured operational state.
6. Docker validation remains authoritative in GitHub Actions when Docker is unavailable locally.

## Non-Goals

This baseline does not add:

- trading behavior
- market data collection
- strategy execution
- websocket infrastructure
- external exchange integrations
