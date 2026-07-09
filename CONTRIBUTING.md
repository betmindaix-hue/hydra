# Contributing

## Scope

HYDRA is developed in platform-focused increments. Contributors must not add:

- live trading
- exchange execution
- Binance or other exchange integrations
- market data collection implementations
- AI features
- websocket infrastructure

## Before Opening A Pull Request

1. Read the relevant ADRs and engineering documents under `docs/`.
2. Keep changes aligned with DDD plus Hexagonal Architecture boundaries.
3. Run local quality gates:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run black --check .`
   - `uv run mypy src tests tools`
   - `uv run python tools/validate_alembic.py`
   - `pre-commit run --all-files`
4. Update documentation for architecture, workflow, observability, or security changes.
5. Review `docs/security/Security Review Checklist.md`.

## Secret And Security Rules

- Never commit `.env`.
- Never commit credentials, private keys, or tokens.
- Keep `.env.example` to placeholders only.
- Do not log secrets or raw database URLs.
- Document security impact in the pull request template.

## Review Expectations

Every pull request should include:

- linked task, ADR, or review document
- summary of repository impact
- tests run
- security impact
- observability impact
- architecture impact
- explicit confirmation that no trading or live execution was added
