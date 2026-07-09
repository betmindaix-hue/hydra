# Engineering Standards

Date: 2026-07-09

## Purpose

This document defines the engineering quality baseline for HYDRA platform work. It applies to all changes in this repository, including non-functional refactors, delivery engineering, tooling, infrastructure, and documentation.

## Scope Rules

The following are out of scope for this engineering hardening phase:

- Market Collector implementation
- Binance integration
- WebSocket infrastructure
- Trading execution
- Paper Trading behavior
- AI features
- Strategy Engine implementation

## Architecture Rules

HYDRA follows a DDD plus Hexagonal Architecture.

Required dependency direction:

- `presentation -> application`
- `application -> domain, ports`
- `adapters -> ports, infrastructure`
- `infrastructure -> ports`

Forbidden dependencies:

- `domain` must not import FastAPI, SQLAlchemy, Redis, Pydantic, or `pydantic-settings`
- `application` must not import FastAPI or SQLAlchemy
- `presentation` must not access the ORM directly

## Tooling Baseline

The repository must pass:

- `pytest`
- `ruff check .`
- `black --check .`
- `mypy src tests tools`

Coverage is collected through Pytest and must remain part of the standard test path.

## Coding Standards

1. Prefer small, typed functions.
2. Keep framework concerns out of `domain/` and `application/`.
3. Use ports for runtime dependencies.
4. Keep changes reproducible and documented.
5. Update `docs/` whenever architecture or engineering workflow changes.

## Git Standards

1. Use Conventional Commits.
2. Run pre-commit locally before pushing.
3. Do not merge code that bypasses architecture fitness tests.
4. Every PR should reference the relevant SDS and engineering documents.

## Release Safety

No platform change is complete until:

- tests pass
- static analysis passes
- Alembic configuration validates
- Docker image builds in CI
- documentation is updated

