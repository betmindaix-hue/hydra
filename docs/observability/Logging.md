# Logging

Date: 2026-07-09

## Format

HYDRA emits newline-delimited JSON logs. Each record includes at minimum:

- `timestamp`
- `level`
- `logger`
- `message`
- `environment`
- `app_name`
- `app_version`
- `correlation_id` when a request scope is active

## Ownership

Logging configuration lives in `src/hydra/infrastructure/logging.py`.

The formatter:

- converts standard library `logging` records into JSON
- enriches logs with runtime metadata
- includes request correlation IDs through shared context

## Startup Diagnostics

At startup HYDRA logs:

- app name
- app version
- environment
- API prefix
- live trading enabled flag
- architecture mode
- database backend type

Only sanitized runtime diagnostics are logged. Raw secrets and database passwords are never emitted.

## Request Logging

HTTP requests are logged from presentation middleware as `request completed` events with:

- `http_method`
- `http_path`
- `status_code`
- `duration_ms`
- `correlation_id`
