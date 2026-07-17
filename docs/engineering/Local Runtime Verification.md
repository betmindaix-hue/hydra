# Local Runtime Verification

Date: 2026-07-17
Scope: HYDRA Engineering Task A7

## Goal

Verify that a developer workstation can bootstrap HYDRA, run the local quality
gates, and inspect runtime health endpoints without depending on Docker image
build success locally.

## Step 1: Verify the Workstation

```powershell
python tools/check_developer_workstation.py
```

If `uv` is not directly on `PATH`, the workstation check accepts a working
fallback through `python -m uv`.

## Step 2: Run the Local Verification Script

```powershell
python tools/local_verify.py
```

This script runs:

- `uv run pytest`
- `uv run ruff check .`
- `uv run black --check .`
- `uv run mypy src tests tools`
- `uv run python tools/validate_alembic.py`
- `uv run python tools/check_repository_security.py`
- `uv run python tools/check_release_readiness.py`
- `uv run python tools/check_operations_readiness.py`

If `uv` is not directly on `PATH`, it automatically falls back to
`python -m uv run ...`.

## Step 3: Run the API

```powershell
uv run uvicorn hydra.main:app --reload
```

Fallback:

```powershell
python -m uv run uvicorn hydra.main:app --reload
```

## Step 4: Verify Runtime Endpoints

PowerShell:

```powershell
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

Git Bash / MINGW64:

```bash
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

Interpretation:

- `/live` should respond even when readiness dependencies are intentionally light
- `/ready` should report readiness-oriented checks
- `/health` should return aggregate runtime status

## Missing Tools

- missing `make`: use direct Python and `uv` commands
- missing Docker: continue local Python verification and treat GitHub Actions as authoritative for Docker build validation
- missing direct `uv`: use `python -m uv ...`

## Explicit Non-Goals

- no production deployment
- no live trading
- no exchange execution
- no exchange credentials
- no real-money operations
