# B3 Backtesting Skeleton Review

Date: 2026-07-18
Scope: HYDRA Engineering Task B3
PR: TBD until pull request is opened
Feature branch: `feat/b3-backtesting-skeleton`

## What Changed

- added pure backtesting domain concepts in `src/hydra/domain/backtesting.py`
- added application DTOs in `src/hydra/application/backtesting_dto.py`
- added `OfflineBacktestingService` in
  `src/hydra/application/backtesting_service.py`
- exported the new backtesting domain and application entry points
- added unit coverage for valid and invalid offline backtesting flows
- updated architecture fitness tests with B3-specific safety guardrails
- added `docs/research_data/Backtesting Skeleton.md`

## Commands Executed

- `python tools/local_verify.py`
- `python -m uv run pytest`
- `python -m uv run ruff check .`
- `python -m uv run black --check .`
- `python -m uv run mypy src tests tools`
- `python -m uv run python tools/validate_alembic.py`
- `python -m uv run python tools/check_repository_security.py`
- `python -m uv run python tools/check_release_readiness.py`
- `python -m uv run python tools/check_operations_readiness.py`
- `python -m uv run python tools/check_developer_workstation.py`
- `python -m uv run pre-commit run --all-files`

## Command Results

- `python tools/local_verify.py`: PASS
  - `132 passed in 7.39s`
  - total coverage: `89%`
  - local verification completed successfully
- `python -m uv run pytest`: PASS
  - `132 passed in 8.17s`
  - total coverage: `89%`
- `python -m uv run ruff check .`: PASS
- `python -m uv run black --check .`: PASS
- `python -m uv run mypy src tests tools`: PASS
- `python -m uv run python tools/validate_alembic.py`: PASS
  - `script_location=alembic`
  - `heads=('20260708_0001',)`
  - `tables=8`
- `python -m uv run python tools/check_repository_security.py`: PASS
- `python -m uv run python tools/check_release_readiness.py`: PASS
- `python -m uv run python tools/check_operations_readiness.py`: PASS
- `python -m uv run python tools/check_developer_workstation.py`: PASS WITH WARNINGS
  - Docker is optional on the developer workstation
  - `make` is optional on the developer workstation
  - summary: `0 failures, 2 warnings`
- `python -m uv run pre-commit run --all-files`: PASS

## Domain Model Summary

- `BacktestId` and `BacktestTimeRange` establish deterministic run identity and
  scope
- `ResearchSignal` models offline research intent using buy, sell, or hold
  semantics
- `SimulatedTrade`, `SimulatedPosition`, and `EquityCurvePoint` model simple
  local simulation state
- `BacktestMetrics` and `BacktestResult` capture outcome quality and dataset
  identity

## Application / Service Summary

- `BacktestRequest` carries the backtest id, dataset, initial cash, optional
  signals, and optional time bounds
- `OfflineBacktestingService` validates boundaries, filters signals to dataset
  timestamps, runs a long-only in-memory simulation, and returns a result
  summary
- no database, filesystem, network, scheduler, or API behavior was added

## Tests Summary

- domain validation rules are covered
- service success and failure scenarios are covered
- ignored out-of-range signals are reported explicitly
- deterministic total return and max drawdown calculations are covered

## Architecture Safety Summary

- backtesting domain remains framework-free
- backtesting application modules remain free of FastAPI and SQLAlchemy
- B3 modules are checked for network client imports
- B3 modules are checked for adapter and infrastructure imports
- exchange, broker, wallet, order-routing, API key, and websocket guardrails
  remain enforced through architecture tests

## Offline-First Compliance

- B3 consumes offline `MarketDataSeries` only
- no live execution concept was introduced
- no external network call was introduced
- no infrastructure adapter was introduced
- no database persistence implementation was introduced

## Scope Compliance

- no live trading was added
- no paper trading was added
- no Binance integration was added
- no exchange adapters were added
- no broker adapters were added
- no WebSocket was added
- no exchange API keys were added
- no external network calls were added
- no API endpoints were added
- no database implementation was added
- no background workers were added
- no order routing or exchange execution behavior was added
- no wallet logic was added

## Remaining Risks

- B3 is intentionally a small synchronous skeleton and does not yet cover
  fees, slippage, partial fills, or richer analytics
- full repository quality-gate and CI/Security evidence must be recorded after
  the pull request is opened
- local workstation validation reports expected optional-tool warnings for
  Docker and `make`

## Final Verdict

PASS WITH WARNINGS
