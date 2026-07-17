# PR Workflow

Date: 2026-07-17
Scope: HYDRA Engineering Task B0

## Purpose

This document defines the expected pull request workflow for Milestone B and
later controlled feature work.

## Milestone B Flow

1. Create a feature branch from `main`.
2. Keep the branch scope aligned to one approved task or sprint objective.
3. Open a pull request before any merge to `main`.
4. Complete the PR template in `.github/pull_request_template.md`.
5. Confirm the change does not add live trading, exchange execution, exchange credentials, or real-money behavior.
6. Run local verification:
   - `python tools/local_verify.py`
   - `python -m uv run pytest`
   - `python -m uv run ruff check .`
   - `python -m uv run black --check .`
   - `python -m uv run mypy src tests tools`
   - `python -m uv run python tools/validate_alembic.py`
   - `python -m uv run python tools/check_repository_security.py`
   - `python -m uv run python tools/check_release_readiness.py`
   - `python -m uv run python tools/check_operations_readiness.py`
   - `python -m uv run python tools/check_developer_workstation.py`
   - `python -m uv run pre-commit run --all-files`
7. Wait for GitHub Actions checks:
   - `CI / quality`
   - `Security / repository-security-baseline`
   - `Security / codeql (python)`
   - `dependency-review` on pull requests where GitHub triggers it
8. Review architecture impact before approval:
   - dependency direction
   - ports-before-adapters
   - domain model before infrastructure
   - architecture tests updated where needed
9. Resolve review conversations before merge.
10. Merge only after the required reviews and checks pass.

## Direct Push Policy

- No direct pushes to `main` for Milestone B feature work.
- Emergency owner-only exceptions should be rare, documented, and followed by a post-change review.

## Scope Guardrails

Milestone B keeps the following out of scope:

- live trading
- exchange execution
- exchange API keys
- Binance integration
- WebSocket infrastructure
- real-money operations

## Evidence Reviewed

- `docs/governance/Governance Model.md`
- `docs/governance/Definition of Done.md`
- `docs/governance/Branch Protection.md`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
