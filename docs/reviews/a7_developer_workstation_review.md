# A7 Developer Workstation Review

Date: 2026-07-17
Scope: HYDRA Engineering Task A7

## What Changed

- Added workstation-focused engineering documents for Windows setup, command parity, and local runtime verification.
- Added `tools/check_developer_workstation.py` for local workstation readiness checks.
- Added `tools/local_verify.py` for consistent local quality gate execution with `uv` fallback support.
- Added focused unit tests for the new workstation and local verification tools.
- Updated CI, Makefile, developer setup guidance, operations docs, contributing guidance, and changelog entries to reflect the workstation baseline.

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
- `python -m uv run pytest`: PASS (`61 passed in 6.12s`, total coverage `97%`)
- `python -m uv run ruff check .`: PASS (`All checks passed!`)
- `python -m uv run black --check .`: PASS (`57 files would be left unchanged.`)
- `python -m uv run mypy src tests tools`: PASS (`Success: no issues found in 55 source files`)
- `python -m uv run python tools/validate_alembic.py`: PASS (`Alembic configuration is valid. script_location=alembic, heads=('20260708_0001',), tables=8`)
- `python -m uv run python tools/check_repository_security.py`: PASS (silent success)
- `python -m uv run python tools/check_release_readiness.py`: PASS (silent success)
- `python -m uv run python tools/check_operations_readiness.py`: PASS (silent success)
- `python -m uv run python tools/check_developer_workstation.py`: PASS with warnings (`Docker` and `make` optional and missing locally)
- `python -m uv run pre-commit run --all-files`: PASS (`ruff`, `black`, `fix end of files`, `trim trailing whitespace`, `check yaml`)

Note: the local shell did not expose `uv` directly on `PATH`, so the required
quality gates were executed with the supported fallback form `python -m uv ...`.

## Workstation Strategy Summary

- HYDRA now distinguishes required workstation tooling from optional tooling.
- Docker is optional locally but remains authoritative in CI for image validation.
- `make` is optional locally.
- `uv` direct mode and `python -m uv` fallback mode are both documented and supported.

## Local Verification Strategy Summary

- `tools/local_verify.py` runs the standard local quality commands without attempting local Docker builds.
- The script supports both direct `uv run ...` execution and `python -m uv run ...` fallback execution.
- Failures are reported step by step with a non-zero exit code.

## Windows/MINGW64/PowerShell Guidance Summary

- New engineering docs cover Windows PowerShell and Git Bash / MINGW64 workflows.
- Command parity is documented for Makefile targets and direct commands.
- Missing `make`, missing Docker, and missing direct `uv` scenarios are now explicitly documented.

## CI Integration Summary

- CI now runs `uv run python tools/check_developer_workstation.py` in addition to all previous checks.
- `tools/local_verify.py` is intentionally not run in CI because CI already executes the underlying steps directly.
- The Security workflow remains unchanged.
- Initial push-time workflow evidence for commit `7223be1aff2fbabce1c34becb5318c0add9bec48`:
  - `CI` run `29610077572`: `completed / failure` at the `Run Pytest` step
  - `Security` run `29610077602`: `completed / success`
- The failing `CI` result could not be reproduced locally with either `python -m uv run pytest` or direct `uv run pytest`, so a follow-up verification commit is used to collect authoritative green evidence.

## Remaining Risks

- The workstation check validates command and file availability but cannot prove every local shell profile is configured correctly.
- Local Docker behavior remains host-dependent, so contributors without Docker still rely on GitHub Actions for Docker build evidence.

## Final Verdict

PASS locally, pending remote CI and Security workflow confirmation.
