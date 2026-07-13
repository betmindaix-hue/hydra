# HYDRA

HYDRA is a single-user quantitative crypto research platform focused on
research, feature engineering, backtesting, paper trading and continuous
evaluation.

The `docs/` directory is the project's single source of truth. This skeleton is
aligned with the SDS documents currently available:

- `docs/00_READ_FIRST.md`
- `docs/01_VISION.md`
- `docs/02_CONSTITUTION.md`
- `docs/03_PRODUCT_REQUIREMENTS.md`
- `docs/04_SYSTEM_ARCHITECTURE.md`
- `docs/05_DATA_MODEL.md`
- `docs/README_NEXT.md`

## What is included

- FastAPI application skeleton
- PostgreSQL-ready SQLAlchemy models
- Redis-ready settings
- Alembic migration setup
- Docker and Docker Compose configuration
- `uv`-based project metadata
- Pytest smoke tests
- Paper trading only, with live trading explicitly disabled

## Architecture summary

Current pipeline:

1. Market Collector
2. Feature Engine
3. Strategy Engine
4. Decision Engine
5. Risk Engine
6. Paper Trading
7. Performance
8. Memory

Core entities:

- MarketBar
- FeatureSet
- StrategySignal
- Decision
- PaperTrade
- PerformanceSnapshot
- Pattern
- Experiment

## Quick start

1. Copy `.env.example` to `.env`.
   Use `.env.local.example` as the preferred workstation reference and `.env.test.example` for automated test overrides.
2. Start infrastructure with `docker compose up -d postgres redis`.
3. If `uv` is not installed yet, run `python -m pip install uv`.
4. Install dependencies with `uv sync`.
5. Run migrations with `uv run alembic upgrade head`.
6. Start the API with `uv run uvicorn hydra.main:app --reload`.
7. Run tests with `uv run pytest`.

## Scope guardrails

- v1 does not include live execution.
- Raw market payloads must be preserved.
- Modules should stay independent.
- Every future architectural change should be reflected in `docs/`.
