# HYDRA

HYDRA is an offline-first quantitative research platform for deterministic
market-data ingestion, strategy research, backtesting, and reporting. Live
trading, exchange integrations, background workers, and network-dependent
runtime features are intentionally out of scope.

The `docs/` directory is authoritative. Milestone B currently rests on these
core references:

- `docs/adr/ADR-0001-hexagonal-architecture.md`
- `docs/adr/ADR-0002-market-data-domain-model.md`
- `docs/adr/ADR-0004-strategy-research-interface.md`
- `docs/adr/ADR-0005-deterministic-fixture-strategy-provider.md`
- `docs/adr/ADR-0006-research-reporting-foundation.md`
- `docs/adr/ADR-0007-end-to-end-offline-research-scenario.md`
- `docs/governance/Definition of Done.md`
- `docs/governance/PR Workflow.md`
- `docs/governance/Milestone B Entry Gate.md`

## Current scope

- Offline market-data domain model and source descriptors
- Offline dataset ingestion through explicit ports
- Deterministic strategy research interface and fixture provider
- Offline backtesting skeleton
- Research reporting foundation
- End-to-end offline research scenario orchestration
- Platform scaffolding with FastAPI, PostgreSQL, Redis, Docker, Alembic, `uv`,
  CI, and security guardrails

## Architecture summary

HYDRA follows Domain-Driven Design with Hexagonal Architecture under
`src/hydra`:

- `domain`: pure Python models and invariants
- `application`: use-case orchestration and DTOs
- `ports`: contracts between application and external concerns
- `adapters`: port implementations such as deterministic fixture providers
- `infrastructure`: configuration and persistence plumbing
- `presentation`: HTTP entrypoints isolated from the domain
- `shared`: cross-cutting support code

Dependency direction is intentionally inward: adapters, infrastructure, and
presentation depend on ports and application services, while the domain remains
framework-free.

## Quick start

1. Copy `.env.example` to `.env`.
2. If `uv` is not installed yet, run `python -m pip install uv`.
3. Install dependencies with `uv sync --frozen --group dev`.
4. Run quality gates with `python tools/local_verify.py`.
5. Start local infrastructure only when needed with `docker compose up -d postgres redis`.
6. Apply migrations with `uv run alembic upgrade head`.
7. Start the presentation skeleton with `uv run uvicorn hydra.main:app --reload`.

## Scope guardrails

- Offline research only; no live trading or exchange connectivity
- No market collector, WebSocket runtime, or real-money operations
- Deterministic and reproducible workflows are preferred over dynamic behavior
- Every architectural or scope change must be reflected in `docs/`
