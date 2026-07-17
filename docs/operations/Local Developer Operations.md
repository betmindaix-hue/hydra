# Local Developer Operations

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Daily Baseline

Use these commands during normal local platform work:

```powershell
python tools/check_developer_workstation.py
python tools/local_verify.py
uv sync --group dev
uv run pytest
uv run ruff check .
uv run black --check .
uv run mypy src tests tools
uv run python tools/validate_alembic.py
uv run python tools/check_developer_workstation.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
pre-commit run --all-files
```

## Local API Checks

After starting the API:

```powershell
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/health
```

Interpretation:

- `/live` should stay dependency-light
- `/ready` should reflect readiness-oriented checks
- `/health` should reflect aggregate runtime status

## Workflow Boundaries

- no live trading
- no exchange execution
- no production deployment automation
- no exchange credentials in local files committed to version control
