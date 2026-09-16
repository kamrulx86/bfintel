import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.hardening_config import get_hardening_settings

_store: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    cfg = get_hardening_settings()
    if cfg.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _allow(key: str, limit: int, window_sec: int) -> bool:
    now = time.monotonic()
    bucket = _store[key]
    while bucket and bucket[0] <= now - window_sec:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def reset_rate_limit_store() -> None:
    """Test helper."""
    _store.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_hardening_settings()
        if not cfg.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in ("/", "/api/health") or path.startswith("/api/setup/status"):
            return await call_next(request)

        ip = _client_ip(request)
        if path.startswith("/api/auth/login") or path.startswith("/api/setup/"):
            key = f"login:{ip}:{path}"
            if not _allow(key, cfg.login_rate_limit, cfg.login_rate_window_seconds):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again later."},
                    headers={"Retry-After": str(cfg.login_rate_window_seconds)},
                )
        elif path.startswith("/api/"):
            key = f"api:{ip}"
            if not _allow(key, cfg.api_rate_limit, cfg.api_rate_window_seconds):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again later."},
                    headers={"Retry-After": str(cfg.api_rate_window_seconds)},
                )

        return await call_next(request)
