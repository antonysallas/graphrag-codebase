import uvicorn
from loguru import logger
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from src.config import get_config
from src.mcp.server import app as mcp_app
from src.mcp.utils import rate_limiter

sse = SseServerTransport("/messages")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        if not rate_limiter.allow(client_id):
            retry_after = rate_limiter.get_retry_after(client_id)
            logger.warning(f"Rate limit exceeded for {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = "100"

        return response

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Check for API key header first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:8]}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"


async def handle_sse(request: Request) -> None:
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_app.run(streams[0], streams[1], mcp_app.create_initialization_options())


async def handle_messages(request: Request) -> None:
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


routes = [
    Route("/sse", endpoint=handle_sse),
    Route("/messages", endpoint=handle_messages, methods=["POST"]),
    Route("/health", endpoint=health),
]

app = Starlette(
    routes=routes,
    middleware=[
        Middleware(RateLimitMiddleware),
    ],
)


def main() -> None:
    config = get_config()
    uvicorn.run(
        app,
        host=config.mcp.server_host,
        port=config.mcp.server_port,
        log_level="info" if not config.mcp.debug else "debug",
    )


if __name__ == "__main__":
    main()
