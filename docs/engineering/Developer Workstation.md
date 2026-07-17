# Developer Workstation

Date: 2026-07-17
Scope: HYDRA Engineering Task A7

## Purpose

This guide defines the supported HYDRA developer workstation baseline for local
bootstrap, validation, and day-to-day platform work.

## Required Tooling

- Python 3.12
- Git
- `uv` directly on `PATH`, or a working fallback through `python -m uv`
- repository files: `pyproject.toml`, `uv.lock`, and `docs/operations/`

## Optional Tooling

- Docker
- `make`

Docker is optional on a developer workstation. GitHub Actions remains the
authoritative Docker validation path.

## First Commands

Use the workstation check before doing deeper setup:

```powershell
python tools/check_developer_workstation.py
```

Then install dependencies:

```powershell
uv sync --group dev
```

If `uv` is not directly on `PATH`, use:

```powershell
python -m uv sync --group dev
```

## Local Validation Baseline

Use the self-check script:

```powershell
python tools/local_verify.py
```

Or run the project commands directly:

```powershell
uv run pytest
uv run ruff check .
uv run black --check .
uv run mypy src tests tools
uv run python tools/validate_alembic.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
```

## Local Runtime Checks

Start the API:

```powershell
uv run uvicorn hydra.main:app --reload
```

Verify:

```powershell
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

Interpretation:

- `/live` is dependency-light
- `/ready` is readiness-oriented
- `/health` is aggregate runtime status

## Explicit Non-Goals

- no production deployment
- no live trading
- no exchange execution
- no exchange credentials
- no real-money operations
