# Runtime Diagnostics Contract

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Startup Diagnostics Fields

HYDRA emits `application startup diagnostics` as structured JSON and may include:

- `app_name`
- `app_version`
- `environment`
- `api_prefix`
- `live_trading_enabled`
- `architecture_mode`
- `database_backend`

`live_trading_enabled` remains `false` in this phase.

## Health Endpoint Response Shape

`/health` returns aggregate status with application metadata and readiness checks:

```json
{
  "status": "ok",
  "app_name": "HYDRA",
  "app_version": "0.1.0",
  "environment": "test",
  "checks": {
    "configuration": "ok",
    "database_session": "ok"
  }
}
```

## Liveness Endpoint Response Shape

`/live` remains dependency-light and returns:

```json
{
  "status": "ok",
  "app_name": "HYDRA",
  "app_version": "0.1.0",
  "environment": "test",
  "checks": {
    "process": "ok"
  }
}
```

## Readiness Endpoint Response Shape

`/ready` remains readiness-oriented and returns:

```json
{
  "status": "ok",
  "app_name": "HYDRA",
  "app_version": "0.1.0",
  "environment": "test",
  "checks": {
    "configuration": "ok",
    "database_session": "ok"
  }
}
```

## Correlation ID Behavior

- HYDRA uses the `X-Correlation-ID` header.
- If the incoming request provides a correlation ID, HYDRA preserves it.
- If the header is missing, HYDRA generates a UUID-based value.
- The response echoes the active correlation ID.
- Request completion logs include the active correlation ID.

## Redaction Rules

Allowed metadata:

- application identity fields
- approved runtime environment name
- API prefix
- architecture mode
- database backend type
- readiness and liveness check names and statuses
- correlation IDs

Forbidden metadata:

- raw database URLs
- Redis passwords
- tokens
- secrets
- exchange credentials
- API keys
- live trading instructions
- exchange execution details

## Endpoint Interpretation

- `/live` is for process liveness only.
- `/ready` is for readiness checks that matter before serving requests.
- `/health` is the aggregate operational status surface.
