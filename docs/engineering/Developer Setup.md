# Developer Setup

Date: 2026-07-09

## Prerequisites

- Python 3.12
- `uv`
- Docker
- Git
- GNU Make or an equivalent `make` implementation for `Makefile` targets

## Initial Setup

1. Copy `.env.example` to `.env`.
2. Install dependencies:
   - `uv sync --group dev`
3. Install git hooks:
   - `uv run pre-commit install`

## Useful Commands

- `make test`
- `make lint`
- `make format`
- `make run`
- `make docker`
- `make alembic-check`

## Local Validation Flow

Before opening a PR, run:

1. `make format`
2. `make lint`
3. `make test`
4. `make alembic-check`
5. `uv run pre-commit run --all-files`

## Notes

- The repository uses `uv.lock` for reproducible dependency resolution.
- Docker validation should succeed in CI even if Docker is unavailable on a contributor machine.
- If `make` is unavailable on Windows, run the equivalent `uv run ...` commands directly.
- Platform-only sprints must not introduce product behavior outside the approved scope.
