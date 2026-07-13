# Configuration Validation

Date: 2026-07-13
Scope: HYDRA Engineering Task A5

## Enforced Rules

| Rule | Behavior |
| --- | --- |
| `environment` must be one of `local`, `test`, `dev`, `staging`, `production-like` | invalid values raise validation errors during settings load |
| `log_level` must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | invalid values raise validation errors |
| `api_prefix` must start with `/` | invalid values raise validation errors |
| `api_prefix` must not end with `/` unless it is exactly `/` | invalid values raise validation errors |
| `database_url` must be present | blank values raise validation errors |
| `redis_url` must be present | blank values raise validation errors |

## Validation Boundaries

- Validation is implemented in `src/hydra/infrastructure/config.py`.
- The shared environment value is framework-free and does not introduce FastAPI, SQLAlchemy, Redis, or Pydantic into the domain layer.
- Application services continue to depend on the `RuntimeSettingsPort` contract, not on configuration parsing details.

## Safety Guarantees

- Startup diagnostics only emit sanitized metadata.
- Raw database URLs, database passwords, Redis passwords, tokens, and exchange credentials are excluded from diagnostic payloads.
- `production-like` remains simulation-only because HYDRA has no runtime switch that enables live trading or exchange execution.

## Automated Verification

Configuration validation is enforced through repository tests and existing CI gates:

- `uv run pytest`
- `uv run ruff check .`
- `uv run black --check .`
- `uv run mypy src tests tools`
- `uv run python tools/validate_alembic.py`
- `uv run python tools/check_repository_security.py`
- `uv run python tools/check_release_readiness.py`
- `pre-commit run --all-files`

The GitHub Actions CI workflow continues to execute the broader quality and Docker build gates on every push and pull request.
