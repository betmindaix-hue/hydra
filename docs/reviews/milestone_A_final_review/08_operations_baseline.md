# Operations Baseline

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

HYDRA has a documented pre-1.0 operations baseline focused on local and CI-safe workflows:

- startup, shutdown, migration, rollback, and recovery runbooks
- CI failure triage guidance
- runtime diagnostics contract
- operations readiness validation script
- endpoint-level operational interpretation for `/live`, `/ready`, and `/health`

This is sufficient for repository-scale engineering work and local runtime verification. It is not a deployment or on-call platform.

## Evidence

- Operations overview: `docs/operations/Operations Overview.md`
- Runtime contract: `docs/operations/Runtime Diagnostics Contract.md`
- Runbooks: `docs/operations/Startup Runbook.md`, `Shutdown Runbook.md`, `Migration Runbook.md`, `Rollback Runbook.md`, `Recovery Runbook.md`, `CI Failure Triage.md`, `Local Developer Operations.md`
- Operations readiness script: `tools/check_operations_readiness.py`
- Operations readiness tests: `tests/test_operations_readiness.py`

Observed operational baseline:

- commands are documented for local validation, tests, Alembic, and workstation checks
- endpoint semantics are explicit and consistent with observability docs
- operational scope excludes production deployment, live trading, exchange execution, and real-money operations

## Commands Or Source Files Reviewed

Commands executed:

- `python -m uv run python tools/check_operations_readiness.py`

Source files reviewed:

- `docs/operations/Operations Overview.md`
- `docs/operations/Runtime Diagnostics Contract.md`
- `docs/operations/CI Failure Triage.md`
- `docs/operations/Local Developer Operations.md`
- `tools/check_operations_readiness.py`
- `tests/test_operations_readiness.py`

## Remaining Risks

- Runbook validation is mostly structural and textual; it does not prove every step is exercised on every workstation profile.
- No deployment automation exists, which is correct for current scope but means future environment rollout work will need new governance and review.
- Local Docker gaps can still block some operators from reproducing image-oriented workflows outside CI.

## Recommendation

Preserve the operations baseline as documentation-first and verification-oriented until the project actually needs a shared runtime. If Milestone B adds offline ingestion or backtesting setup, update runbooks in the same pull request as the capability.
