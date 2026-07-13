# Rollback Runbook

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Define how rollback is handled during pre-1.0 HYDRA development.

## Current Rollback Model

HYDRA does not define a production deployment rollback path yet. Rollback in
this phase is limited to repository state, local schema state, and disposable
development environments.

## Repository Rollback

Use standard Git workflows to move to a known-good commit in a local branch or
temporary recovery branch. Preserve review history and avoid destructive commands
unless they are explicitly approved.

## Database Rollback

If the migration chain supports a downgrade and the target environment is safe:

```powershell
uv run alembic downgrade -1
```

If downgrade safety is unclear:

1. stop the API
2. snapshot the local or dev database if possible
3. rebuild from a known-good schema state rather than guessing

## Operational Boundaries

- pre-1.0 rollback is for local and dev recovery, not production deployment
- no live trading rollback path exists
- no exchange execution rollback path exists
- no real-money operational rollback is supported
