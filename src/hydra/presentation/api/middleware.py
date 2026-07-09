import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from hydra.shared.correlation import (
    generate_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = logging.getLogger("hydra.http")

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        incoming_correlation_id = request.headers.get(CORRELATION_ID_HEADER, "").strip()
        correlation_id = incoming_correlation_id or generate_correlation_id()
        token = set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id
        started_at = perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            self._logger.info(
                "request completed",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code if response is not None else 500,
                },
            )
            reset_correlation_id(token)

        assert response is not None
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
