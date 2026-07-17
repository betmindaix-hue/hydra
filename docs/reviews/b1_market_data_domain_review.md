# B1 Market Data Domain Review

Date: 2026-07-17
Scope: HYDRA Engineering Task B1 Hardening
PR: https://github.com/betmindaix-hue/hydra/pull/11
Feature branch: `feat/b1-market-data-domain`

## What Changed

- enforced strict offline-first behavior in `src/hydra/domain/market_data.py`
- prevented `DataSourceDescriptor` from accepting `offline_only=False`
- added a regression test proving mixed-mode or live-like source descriptors are rejected
- investigated the failed Security workflow and fixed the repository-level root cause
- moved PR #11 from draft to ready for review after CI and Security passed

## Security Failure Investigation

Failed workflow:

- workflow: `Security`
- run id: `29616456397`
- commit: `c3f7edb7ebc0868954275f3b1326fbbf21ede7c4`
- failing job: `dependency-review`
- failing step: `Dependency review`

Observed root cause:

- GitHub reported: `Dependency review is not supported on this repository.`
- the annotation pointed to repository settings and required `Dependency graph` to be enabled

Applied fix:

- enabled `Dependency graph` in repository security settings at
  `https://github.com/betmindaix-hue/hydra/settings/security_analysis`
- did not weaken the workflow
- did not remove `CodeQL`
- did not remove `repository-security-baseline`
- did not disable `dependency-review`

Verification after fix:

- `Security` pull request run `29617021822`: `Success`
- `dependency-review`: `Success in 7s`
- `repository-security-baseline`: `Success in 7s`
- `codeql (python)`: `Success in 53s`

## Domain Hardening Summary

- `DataSourceDescriptor` now rejects any non-offline configuration
- string rendering always communicates `offline-only`
- B1 can no longer construct a mixed-mode source descriptor

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
  - `85 passed in 6.98s`
  - local verify completed successfully
- `python -m uv run pytest`: PASS
  - `85 passed in 8.06s`
  - total coverage: `96%`
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
  - Docker is optional on the local workstation
  - `make` is optional on the local workstation
- `python -m uv run pre-commit run --all-files`: PASS

## CI and PR Status

- PR link: https://github.com/betmindaix-hue/hydra/pull/11
- feature branch: `feat/b1-market-data-domain`
- PR state: `ready for review`
- `CI` pull request run `29617021827`: `Success`
- `Security` pull request run `29617021822`: `Success`
- `CI` push run `29617020043`: `Success`

## Scope Compliance

- no live market data collection added
- no Binance integration added
- no exchange adapters added
- no WebSocket added
- no trading added
- no AI added
- no strategies added
- no paper trading added
- no exchange execution added
- no order routing added
- no wallet logic added
- no API keys added
- no real-money operations added
- no background workers added
- no external network calls added
- no database persistence implementation added
- no API endpoints added

## Remaining Risks

- GitHub Actions emits Node.js 20 deprecation warnings for several third-party actions even though the runs pass
- the repository still contains temporary overlap between earlier scaffold entities and the newer market data domain model

## Final Verdict

PASS WITH WARNINGS
