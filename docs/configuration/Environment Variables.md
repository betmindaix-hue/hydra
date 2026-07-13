# Environment Variables

Date: 2026-07-13
Scope: HYDRA Engineering Task A5

## Variables

| Variable | Required | Placeholder example | Description |
| --- | --- | --- | --- |
| `HYDRA_APP_NAME` | No | `<app_name>` | Service display name |
| `HYDRA_APP_VERSION` | No | `<app_version>` | Runtime version identifier |
| `HYDRA_ENVIRONMENT` | Yes | `<environment: local|test|dev|staging|production-like>` | Approved runtime environment |
| `HYDRA_API_PREFIX` | Yes | `<api_prefix: /api/v1>` | API routing prefix |
| `HYDRA_DATABASE_URL` | Yes | `postgresql+psycopg://<db_user>:<db_password>@<db_host>:<db_port>/<db_name>` | Primary relational database URL |
| `HYDRA_REDIS_URL` | Yes | `redis://<redis_host>:<redis_port>/<redis_db>` | Redis connection URL |
| `HYDRA_LOG_LEVEL` | Yes | `<log_level: DEBUG|INFO|WARNING|ERROR|CRITICAL>` | Structured logging threshold |

## Template Files

- `.env.example` is the generic contract template.
- `.env.local.example` is the workstation-oriented template.
- `.env.test.example` is the automated test-oriented template.

All example files stay in version control because they contain placeholders only. Local `.env` files remain untracked and must never be committed.
