# Recovery Runbook

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Recover local or dev HYDRA environments after a failed startup, migration, or
validation event.

## Local Recovery Procedure

1. Stop the API process.
2. Re-check configuration files and placeholders.
3. Re-run deterministic validation commands:

```powershell
uv run pytest
uv run python tools/validate_alembic.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
```

4. Restart dependencies:

```powershell
docker compose restart postgres redis
```

5. Retry the local health checks:

```powershell
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

## Dev Environment Recovery

- confirm the selected environment is `dev`, not `production-like`
- prefer redeploying a known-good commit over manual hotfixes in the running environment
- confirm migrations and runtime configuration before reopening the environment to other developers

## Not Supported

- production deployment recovery
- live trading recovery
- exchange execution recovery
