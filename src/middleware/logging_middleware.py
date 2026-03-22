import time
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("gold_tier")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {duration_ms}ms",
            extra={"correlation_id": correlation_id, "duration_ms": duration_ms},
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response
