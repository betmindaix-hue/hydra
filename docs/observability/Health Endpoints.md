# Health Endpoints

Date: 2026-07-09

## Endpoints

HYDRA exposes these operational endpoints:

- `/health`
- `/live`
- `/ready`

For backward compatibility, `/api/v1/health` returns the same structured health payload as `/health`.

## Response Shape

All operational endpoints return structured JSON:

```json
{
  "status": "ok",
  "app_name": "HYDRA",
  "app_version": "0.1.0",
  "environment": "development",
  "checks": {
    "configuration": "ok",
    "database_session": "ok"
  }
}
```

## Endpoint Semantics

### `/live`

- validates process liveness only
- does not require database or Redis access
- returns `checks.process = ok`

### `/ready`

- validates runtime configuration loading
- validates database session wiring
- does not require external production services in unit tests

### `/health`

- returns an aggregate operational status
- includes app metadata and current readiness checks

## Current Checks

- `configuration`
- `database_session`
