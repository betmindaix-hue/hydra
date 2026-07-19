# B7 End-to-End Offline Research Scenario Review

Date: 2026-07-19
Scope: HYDRA Engineering Task B7
PR: TBD until pull request is opened
Feature branch: `feat/b7-end-to-end-offline-research-scenario`
PR state: Not opened yet

## What Changed

- added `OfflineResearchScenarioRequest`, `OfflineResearchScenarioStage`,
  `OfflineResearchScenarioError`, and `OfflineResearchScenarioResult` in
  `src/hydra/application/offline_research_scenario_dto.py`
- added `OfflineResearchScenarioService` in
  `src/hydra/application/offline_research_scenario_service.py`
- updated `src/hydra/application/__init__.py` with a minimal scenario service
  export
- added deterministic end-to-end and failure-path coverage in
  `tests/test_offline_research_scenario_service.py`
- extended `tests/test_architecture_layers.py` with B7-specific guardrails for
  framework imports, outer-layer imports, filesystem/network/analysis/export
  imports, keyword scans, wall-clock calls, and direct B5 adapter imports
- added `docs/adr/ADR-0007-end-to-end-offline-research-scenario.md`
- added `docs/research_data/End-to-End Offline Research Scenario.md`

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
  - `267 passed in 8.48s`
  - total coverage: `88%`
  - local verification completed successfully
- `python -m uv run pytest`: PASS
  - `267 passed in 8.38s`
  - total coverage: `88%`
- `python -m uv run ruff check .`: PASS
- `python -m uv run black --check .`: PASS
- `python -m uv run mypy src tests tools`: PASS
- `python -m uv run python tools/validate_alembic.py`: PASS
  - `script_location=alembic`
  - `heads=('20260708_0001',)`
  - `tables=8`
- `python -m uv run python tools/check_repository_security.py`: PASS
  - completed with exit code `0`
- `python -m uv run python tools/check_release_readiness.py`: PASS
  - completed with exit code `0`
- `python -m uv run python tools/check_operations_readiness.py`: PASS
  - completed with exit code `0`
- `python -m uv run python tools/check_developer_workstation.py`: PASS WITH WARNINGS
  - Docker is optional on the developer workstation
  - `make` is optional on the developer workstation
  - summary: `0 failures, 2 warnings`
- `python -m uv run pre-commit run --all-files`: PASS

## Scenario Summary

- B7 connects B2 ingestion, B4 strategy research, B3 backtesting, and B6
  reporting in one deterministic application-level execution path
- the scenario request carries explicit offline records, identifiers, time
  bounds, initial cash, provider injection, and optional presentation-neutral
  notes
- the scenario result carries each stage output and exposes a `successful`
  property that only turns true when all stages complete cleanly

## Service Summary

- `OfflineResearchScenarioService` validates request type before orchestration
- ingestion must return exactly one `MarketDataSeries`
- strategy research is constructed from the injected B4 port contract, not the
  B5 concrete provider
- backtesting and reporting only execute after the previous stage succeeds
- later-stage failures preserve earlier successful outputs

## Tests Summary

- the happy-path test proves the full offline scenario works with deterministic
  BUY and SELL fixture signals
- repeated execution with the same request returns equal results
- failure-path tests cover invalid request input, ingestion failure, zero
  series, multiple series, strategy failure, provider error, backtesting
  failure, and reporting failure
- request validation tests cover blank identifiers, invalid initial cash,
  naive timestamps, title/note normalization, and immutable storage
- tests explicitly prove no file writes occur and that stage order remains
  strategy research -> backtesting -> reporting

## Architecture Safety Summary

- B7 DTO and service modules remain framework-free with respect to FastAPI,
  SQLAlchemy, Redis, Pydantic, and `pydantic-settings`
- B7 DTO and service modules do not import adapters, infrastructure, or
  presentation layers
- B7 DTO and service modules are checked for filesystem, network, analysis,
  and export library imports
- B7 keyword guards remain active for exchange/live-execution/strategy
  automation vocabulary
- B7 service is checked for wall-clock calls and direct import of the B5
  deterministic fixture provider

## Offline-First Compliance

- the scenario runs only on in-memory offline inputs
- no live connectivity was introduced
- no external network call was introduced
- no persistence implementation was introduced
- no API route, CLI, scheduler, or workflow runner was introduced

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
- no scheduler was added
- no CLI was added
- no order routing or exchange execution behavior was added
- no wallet logic was added
- no AI strategy generation was added
- no ML models were added
- no automatic trading was added
- no production strategy implementation was added
- no indicator engine was added
- no moving-average strategy was added
- no RSI strategy was added
- no optimizer was added
- no chart rendering was added
- no PDF export was added
- no HTML export was added
- no filesystem report writer was added
- no dashboard was added

## Remaining Risks

- PR and GitHub workflow evidence are still pending because the draft pull
  request has not been opened yet
- Docker validation remains authoritative in CI even though local quality gates
  passed without requiring Docker on the workstation
- B7 intentionally covers a single deterministic scenario seam and does not yet
  address richer multi-run orchestration, which would require a separate ADR

## Final Verdict

PASS WITH WARNINGS
