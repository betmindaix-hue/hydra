# C2 Research Run Ranking and Selection Review

Date: 2026-07-20
Status: Local quality gates passed; PR evidence pending

## Pull Request

- PR: TBD until pull request is opened
- Feature branch: `feat/c2-research-run-ranking-selection`

## What Changed

- Added application-layer DTOs for ranking metrics, directions, eligibility,
  ranking specifications, ranking entries, exclusion reasons, and ranking
  results.
- Added `ResearchRunRankingService` for deterministic ranking and top-run
  selection over existing C1 `ResearchRunRecord` values.
- Added focused C2 tests for default metric directions, explicit directions,
  eligibility filters, exclusion behavior, deterministic tie-breaking, limit
  handling, and storage-independent behavior.
- Added C2-specific architecture guardrails for framework, persistence,
  network, analysis, rendering, and runtime-boundary protection.
- Added ADR-0010 and the C2 research usability note.

## Commands Executed

### Targeted verification completed before full gates

```text
python -m uv run pytest tests/test_research_run_ranking_service.py tests/test_architecture_layers.py
python -m uv run ruff check src/hydra/application/research_run_ranking_dto.py src/hydra/application/research_run_ranking_service.py src/hydra/application/__init__.py tests/test_research_run_ranking_service.py tests/test_architecture_layers.py
python -m uv run mypy src/hydra/application/research_run_ranking_dto.py src/hydra/application/research_run_ranking_service.py tests/test_research_run_ranking_service.py tests/test_architecture_layers.py
python -m uv run black --check src/hydra/application/research_run_ranking_dto.py src/hydra/application/research_run_ranking_service.py src/hydra/application/__init__.py tests/test_research_run_ranking_service.py tests/test_architecture_layers.py
```

### Full quality gates

```text
python tools/local_verify.py
python -m uv run pytest
python -m uv run ruff check .
python -m uv run black --check .
python -m uv run mypy src tests tools
python -m uv run python tools/validate_alembic.py
python -m uv run python tools/check_repository_security.py
python -m uv run python tools/check_release_readiness.py
python -m uv run python tools/check_operations_readiness.py
python -m uv run python tools/check_developer_workstation.py
python -m uv run pre-commit run --all-files
```

## Command Results

### Targeted verification

- `pytest` result: PASS
  - Output summary: `121 passed in 4.72s`
- `ruff check` result: PASS
  - Output summary: `All checks passed!`
- `mypy` result: PASS
  - Output summary: `Success: no issues found in 4 source files`
- `black --check` result: PASS
  - Output summary: `5 files would be left unchanged.`

### Full quality gates

- `python tools/local_verify.py` result: PASS
  - Output summary: local verification completed successfully after passing
    pytest, Ruff, Black, Mypy, Alembic validation, repository security, release
    readiness, and operations readiness.
- `python -m uv run pytest` result: PASS
  - Output summary: `400 passed in 10.54s`
- `python -m uv run ruff check .` result: PASS
  - Output summary: `All checks passed!`
- `python -m uv run black --check .` result: PASS
  - Output summary: `91 files would be left unchanged.`
- `python -m uv run mypy src tests tools` result: PASS
  - Output summary: `Success: no issues found in 89 source files`
- `python -m uv run python tools/validate_alembic.py` result: PASS
  - Output summary:
    `Alembic configuration is valid. script_location=alembic, heads=('20260708_0001',), tables=8`
- `python -m uv run python tools/check_repository_security.py` result: PASS
  - Output summary: no stdout, exit code `0`
- `python -m uv run python tools/check_release_readiness.py` result: PASS
  - Output summary: no stdout, exit code `0`
- `python -m uv run python tools/check_operations_readiness.py` result: PASS
  - Output summary: no stdout, exit code `0`
- `python -m uv run python tools/check_developer_workstation.py` result: PASS WITH WARNINGS
  - Output summary: `0 failures, 2 warnings`
  - Warning details:
    - Docker is optional locally; GitHub Actions remains the authoritative
      Docker validation path.
    - `make` is optional locally; `uv` and direct repository commands remain
      available.
- `python -m uv run pre-commit run --all-files` result: PASS
  - Output summary: Ruff, Black, EOF fixer, trailing whitespace, and YAML
    validation hooks passed.

## Coverage Result

- Targeted run coverage is not the release signal for C2 because it executes a
  subset of the suite.
- Full-suite coverage result: `91%`
- Required threshold: at least `90%`

## Architecture Safety Summary

- C2 remains inside the application layer.
- No new port, adapter, infrastructure, or presentation surface was added.
- The ranking service consumes C1 `ResearchRunRecord` values and does not depend
  on catalog storage.
- C2 guardrails block framework imports, persistence modules, network clients,
  analysis/rendering libraries, and prohibited runtime keywords.
- The service remains deterministic and avoids wall-clock behavior.

## Research Usability Summary

- C2 adds deterministic run ranking and top-run selection on top of C1 records.
- Engineers can express basic eligibility rules and retrieve stable exclusions.
- Tie-breaking is explicit and stable under equal metrics.

## Offline-First Compliance

- No live runtime integration was introduced.
- No external network call is required.
- No file or database persistence was added.
- The ranking service does not execute research and does not rerun scenarios.

## Scope Compliance

- No live trading was added.
- No paper trading was added.
- No Binance integration was added.
- No exchange adapter was added.
- No broker adapter was added.
- No WebSocket behavior was added.
- No API endpoint was added.
- No database implementation was added.
- No file, JSON, or CSV persistence was added.
- No CLI, dashboard, chart rendering, or export behavior was added.
- No AI, ML, or automatic strategy behavior was added.

## Remaining Risks

- CI and Security workflow outcomes are pending until the draft PR is opened and
  the remote checks complete.
- Future weighted ranking or durable storage needs will require a separate
  design path and must not be inferred from C2.

## Final Verdict

PENDING
