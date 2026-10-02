import time
from collections import defaultdict
from threading import Lock
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import metrics_registry


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per client identifier."""

    def __init__(self, default_limit: int = 120, auth_limit: int = 20, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_key: str, is_auth: bool = False) -> tuple[bool, int, int]:
        """Returns (is_allowed, remaining, retry_after_seconds)."""
        limit = self.auth_limit if is_auth else self.default_limit
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Evict timestamps outside current sliding window
            timestamps = [t for t in self._requests[client_key] if t > window_start]
            self._requests[client_key] = timestamps

            if len(timestamps) >= limit:
                oldest_in_window = timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest_in_window)))
                return False, 0, retry_after

            # Record this request
            timestamps.append(now)
            remaining = max(0, limit - len(timestamps))
            return True, remaining, 0

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter()


class SecurityAndObservabilityMiddleware(BaseHTTPMiddleware):
    """Enforces OWASP security headers, sliding-window rate limiting,

    and Prometheus request metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start_time = time.time()
        path = request.url.path

        # 1. Exempt health, doc, and metrics probes from rate limiting
        is_exempt = path in ("/healthz", "/readyz", "/metrics", "/docs", "/openapi.json")

        if not is_exempt:
            client_ip = request.client.host if request.client else "127.0.0.1"
            auth_header = request.headers.get("Authorization")
            client_id = f"{client_ip}:{auth_header[:16]}" if auth_header else client_ip

            is_auth_route = "/auth/login" in path
            allowed, remaining, retry_after = rate_limiter.is_allowed(client_id, is_auth=is_auth_route)

            if not allowed:
                metrics_registry.inc_counter(
                    "agentpulse_http_requests_total",
                    method=request.method,
                    endpoint=path,
                    status=str(status.HTTP_429_TOO_MANY_REQUESTS),
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "type": "https://agentpulse.dev/errors/rate-limit-exceeded",
                        "title": "RATE_LIMIT_EXCEEDED",
                        "status": 429,
                        "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "instance": str(request.url),
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        # 2. Process request
        response: Response = await call_next(request)
        duration = time.time() - start_time

        # 3. Record Prometheus metrics
        metrics_registry.inc_counter(
            "agentpulse_http_requests_total",
            method=request.method,
            endpoint=path,
            status=str(response.status_code),
        )
        metrics_registry.observe_histogram(
            "agentpulse_http_request_duration_seconds",
            duration,
            endpoint=path,
        )

        # 4. Attach OWASP Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        return response
