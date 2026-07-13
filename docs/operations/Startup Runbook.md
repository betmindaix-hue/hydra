# Startup Runbook

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Start HYDRA locally with validated configuration and confirm the API is healthy.

## Preconditions

- Python 3.12
- `uv`
- Docker or another way to provide PostgreSQL and Redis locally
- a local `.env` derived from `.env.example` or `.env.local.example`

## Startup Sequence

1. Validate the repository state.

```powershell
uv run pytest
uv run python tools/validate_alembic.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
```

2. Start local dependencies.

```powershell
docker compose up -d postgres redis
```

3. Apply database migrations.

```powershell
uv run alembic upgrade head
```

4. Start the API.

```powershell
uv run uvicorn hydra.main:app --reload
```

5. Validate runtime endpoints.

```powershell
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

## Expected Results

- `/live` returns process liveness without requiring readiness dependencies.
- `/ready` returns readiness-oriented checks for configuration and database session wiring.
- `/health` returns aggregate status plus application metadata.

## Not Supported

- production deployment
- live trading
- exchange execution
- exchange credentials
