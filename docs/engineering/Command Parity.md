# Command Parity

Date: 2026-07-17
Scope: HYDRA Engineering Task A7

## Purpose

This document maps Makefile targets and direct commands across PowerShell and
Git Bash / MINGW64.

## Command Table

| Purpose | Make target | Direct command | `uv` fallback |
| --- | --- | --- | --- |
| Workstation readiness | `make workstation-check` | `python tools/check_developer_workstation.py` | same direct Python command |
| Local verification | `make local-verify` | `python tools/local_verify.py` | same direct Python command |
| Tests | `make test` | `uv run pytest` | `python -m uv run pytest` |
| Lint and type checks | `make lint` | `uv run ruff check .`<br>`uv run black --check .`<br>`uv run mypy src tests tools` | `python -m uv run ruff check .`<br>`python -m uv run black --check .`<br>`python -m uv run mypy src tests tools` |
| Format | `make format` | `uv run ruff check . --fix`<br>`uv run black .` | `python -m uv run ruff check . --fix`<br>`python -m uv run black .` |
| Alembic validation | `make alembic-check` | `uv run python tools/validate_alembic.py` | `python -m uv run python tools/validate_alembic.py` |
| Operations readiness | `make ops-check` | `uv run python tools/check_operations_readiness.py` | `python -m uv run python tools/check_operations_readiness.py` |
| Local API run | `make run` | `uv run uvicorn hydra.main:app --reload` | `python -m uv run uvicorn hydra.main:app --reload` |

## Notes

- PowerShell and Git Bash / MINGW64 should produce equivalent outcomes.
- If `make` is missing, use the direct commands.
- If Docker is missing, rely on GitHub Actions for Docker image validation.

## Explicit Non-Goals

- no production deployment
- no live trading
- no exchange execution
- no exchange credentials
- no real-money operations
