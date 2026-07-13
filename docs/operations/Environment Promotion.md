# Environment Promotion

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Describe how HYDRA environments progress during pre-1.0 platform work.

## Promotion Path

```text
local -> test -> dev -> staging -> production-like
```

## Promotion Checks

Before moving confidence to the next environment tier:

```powershell
uv run pytest
uv run python tools/validate_alembic.py
uv run python tools/check_repository_security.py
uv run python tools/check_release_readiness.py
uv run python tools/check_operations_readiness.py
```

Confirm these endpoints remain healthy in the target environment:

- `/live`
- `/ready`
- `/health`

## Constraints

- `staging` is future-facing and not production
- `production-like` is operational simulation only
- no production deployment process is defined here
- no live trading or exchange execution is supported in any promotion step
