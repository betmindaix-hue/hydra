# CI Failure Triage

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Provide a deterministic path for investigating CI failures without widening the
platform scope.

## First Response

1. Open the failing GitHub Actions run.
2. Identify the first failing step.
3. Reproduce that step locally whenever the tool is available.

## Common Failure Commands

```powershell
uv run ruff check .
uv run black --check .
uv run mypy src tests tools
uv run pytest
uv run python tools/validate_alembic.py
uv run python tools/check_developer_workstation.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
```

## Triage Rules

- if `/live`, `/ready`, or `/health` behavior changed unexpectedly, review observability tests first
- if startup diagnostics changed, verify that secrets are still redacted
- if the developer workstation check fails, confirm `python`, `git`, `uv`, `pyproject.toml`, `uv.lock`, and `docs/operations/` are present
- if Alembic validation failed, use the migration runbook before changing runtime code
- if only Docker failed locally, treat CI as the authoritative build path when the local Docker CLI is unavailable

## Escalation

- document the failing command and first error line
- link the relevant review document
- involve architecture or security review when the failure affects diagnostics, CI policy, or secret handling

## Non-Goals

- production deployment triage
- live trading triage
- exchange execution triage
