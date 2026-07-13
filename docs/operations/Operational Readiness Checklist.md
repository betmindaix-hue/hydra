# Operational Readiness Checklist

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Checklist

- [ ] `docs/operations/` documents are present and current
- [ ] runtime configuration matches the documented contract
- [ ] `uv run pytest` passes
- [ ] `uv run python tools/validate_alembic.py` passes
- [ ] `uv run python tools/check_repository_security.py` passes
- [ ] `uv run python tools/check_release_readiness.py` passes
- [ ] `uv run python tools/check_operations_readiness.py` passes
- [ ] `/live` is healthy
- [ ] `/ready` is healthy
- [ ] `/health` is healthy
- [ ] startup diagnostics remain redacted and secret-safe
- [ ] no live trading or exchange execution behavior was added

## Current Limitations

- no production deployment workflow
- no deployment automation
- no live trading
- no exchange execution
- no real-money operations
