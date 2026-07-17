# Developer Setup

Date: 2026-07-17

## Prerequisites

- Python 3.12
- Git
- `uv`, or a working fallback through `python -m uv`
- Docker for optional local infrastructure and image workflows
- GNU Make or an equivalent `make` implementation for `Makefile` targets when available

## Initial Setup

1. Copy `.env.example` to `.env`.
   Use `.env.local.example` for workstation-oriented placeholder guidance and `.env.test.example` for automated test profile guidance.
2. Install dependencies:
   - `uv sync --group dev`
   - fallback: `python -m uv sync --group dev`
3. Install git hooks:
   - `uv run pre-commit install`
   - fallback: `python -m uv run pre-commit install`
4. Validate the workstation:
   - `python tools/check_developer_workstation.py`

## Useful Commands

- `make test`
- `make lint`
- `make format`
- `make run`
- `make docker`
- `make alembic-check`
- `make ops-check`
- `make workstation-check`
- `make local-verify`

## Local Validation Flow

Before opening a PR, run:

1. `python tools/check_developer_workstation.py`
2. `python tools/local_verify.py`
3. `uv run pre-commit run --all-files`

## Notes

- The repository uses `uv.lock` for reproducible dependency resolution.
- Docker validation should succeed in CI even if Docker is unavailable on a contributor machine.
- If `make` is unavailable on Windows, run the equivalent direct `python` and `uv` commands instead.
- If `uv` is not directly on `PATH`, use `python -m uv ...`.
- See `docs/engineering/Developer Workstation.md`, `Windows Setup.md`, `Command Parity.md`, and `Local Runtime Verification.md` for workstation-specific guidance.
- Platform-only sprints must not introduce product behavior outside the approved scope.
