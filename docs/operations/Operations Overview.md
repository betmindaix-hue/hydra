# Operations Overview

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Purpose

This directory defines HYDRA's first operations baseline for pre-1.0 development.
It is command-oriented and limited to local, test, dev, staging, and
production-like operational simulation workflows.

## Supported Operational Scope

- local startup and shutdown
- configuration validation
- automated test execution
- Alembic validation
- local API health verification through `/live`, `/ready`, and `/health`
- CI failure triage
- migration troubleshooting
- rollback guidance for pre-1.0 development
- recovery steps for local and dev environments

## Explicit Non-Goals

- production deployment
- deployment automation
- live trading
- exchange execution
- exchange credentials
- real-money operations

In practical terms: no live trading and no exchange execution are supported by
HYDRA in this phase.

## Core Operational Commands

```powershell
docker compose up -d postgres redis
uv sync --group dev
uv run pytest
uv run python tools/validate_alembic.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
uv run uvicorn hydra.main:app --reload
```

## Endpoint Interpretation

- `/live` verifies process liveness only.
- `/ready` verifies runtime configuration loading and database session wiring.
- `/health` returns the aggregate operational status using the current readiness checks.

See the dedicated runbooks in this directory for step-by-step procedures.
