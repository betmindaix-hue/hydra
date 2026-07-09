# Correlation IDs

Date: 2026-07-09

## Behavior

HYDRA uses `X-Correlation-ID` for HTTP request correlation.

Rules:

1. If a client sends `X-Correlation-ID`, HYDRA preserves it.
2. If the header is missing, HYDRA generates a UUID-based value.
3. The correlation ID is added to the response headers.
4. Request-scope logs include the correlation ID automatically.

## Implementation

- `src/hydra/presentation/api/middleware.py` manages the header and request lifecycle
- `src/hydra/shared/correlation.py` stores the active correlation ID in a framework-agnostic context variable
- `src/hydra/infrastructure/logging.py` enriches logs with the active correlation ID

## Boundaries

- domain code never imports FastAPI or logging infrastructure
- correlation handling stays outside domain and application business rules
- presentation does not push FastAPI types into domain
