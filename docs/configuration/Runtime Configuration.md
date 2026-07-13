# Runtime Configuration

Date: 2026-07-13
Scope: HYDRA Engineering Task A5

## Ownership

- `src/hydra/infrastructure/config.py` parses runtime settings with `pydantic-settings`.
- `src/hydra/adapters/runtime_settings.py` maps infrastructure settings into `RuntimeSettings`.
- `src/hydra/ports/runtime_settings.py` defines the application-facing contract.
- `src/hydra/shared/runtime_environment.py` defines the framework-free environment value.

## Configuration Sources

1. Safe defaults in `Settings`
2. Environment variables prefixed with `HYDRA_`
3. A local `.env` file when present

Defaults are intentionally limited to local-safe scaffolding. They are not a secret store and they are not a deployment strategy.

## Configuration Contract

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `app_name` | `str` | `HYDRA` | Human-readable service name |
| `app_version` | `str` | `0.1.0` | Runtime version string |
| `environment` | `RuntimeEnvironment` | `local` | Allowed values are centrally defined in `shared/` |
| `api_prefix` | `str` | `/api/v1` | Must start with `/` |
| `database_url` | `str` | `postgresql+psycopg://placeholder:placeholder@localhost:5432/hydra_local` | Fake local placeholder credentials only |
| `redis_url` | `str` | `redis://localhost:6379/0` | Required runtime dependency even when Redis usage is deferred |
| `log_level` | `str` | `INFO` | Normalized to uppercase and validated against the approved set |

## Dependency Direction

```mermaid
flowchart LR
    infra["infrastructure/config.py"] --> adapter["adapters/runtime_settings.py"]
    adapter --> port["ports/runtime_settings.py"]
    port --> app["application services"]
    app --> presentation["presentation routers"]
    shared["shared/runtime_environment.py"] --> infra
    shared --> port
```

## Diagnostic Alignment

Startup diagnostics may expose:

- `app_name`
- `app_version`
- `environment`
- `api_prefix`
- `database_backend`
- `architecture_mode`
- `live_trading_enabled`

Startup diagnostics must never expose raw connection strings, passwords, tokens, or exchange credentials.
