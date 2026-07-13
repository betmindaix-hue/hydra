# Migration Runbook

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Validate and apply schema migrations safely during pre-1.0 development.

## Validation First

Before applying a migration, validate the repository and Alembic wiring:

```powershell
uv run python tools/validate_alembic.py
uv run pytest
```

## Apply Migrations

Run the latest migration head:

```powershell
uv run alembic upgrade head
```

Inspect the current revision state:

```powershell
uv run alembic current
uv run alembic heads
```

## When Migrations Fail

1. Stop and read the first error, not just the last stack frame.
2. Re-run Alembic validation:

```powershell
uv run python tools/validate_alembic.py
```

3. Verify configuration values in `.env`.
4. Confirm the target database is the expected local, test, or dev database.
5. Review the generated migration script before retrying.

## Safety Notes

- Do not improvise production deployment recovery from this runbook.
- Do not introduce live trading or exchange execution logic into migration scripts.
- Keep migrations deterministic and version-controlled.
