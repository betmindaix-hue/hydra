# Dependency Inventory

Date: 2026-07-10

## Supply Chain Baseline

- Package manager: `uv`
- Lockfile: `uv.lock`
- Primary manifest: `pyproject.toml`
- Container build: `Dockerfile` installs from `uv.lock` using `uv sync --frozen`
- Dependency update governance: GitHub Dependabot weekly updates for Python, GitHub Actions, and Docker

## Direct Runtime Dependencies

- `alembic`
- `fastapi`
- `psycopg[binary]`
- `pydantic-settings`
- `redis`
- `sqlalchemy`
- `uvicorn[standard]`

## Direct Development Dependencies

- `black`
- `httpx`
- `mypy`
- `pre-commit`
- `pytest`
- `pytest-cov`
- `ruff`

## Update Process

1. Dependabot proposes weekly updates.
2. Review dependency intent and change scope.
3. Run the repository quality gates.
4. Confirm CI and Docker build pass.
5. Merge only after security and architecture review expectations are satisfied.

## Notes

- `uv.lock` is the authoritative dependency snapshot for reproducible installs.
- This document is a lightweight inventory baseline, not a full transitive SBOM export.
