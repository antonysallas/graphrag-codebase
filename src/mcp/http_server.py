from typing import Any

import uvicorn
from loguru import logger
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from src.config import get_config
from src.mcp.server import app as mcp_app
from src.mcp.utils import rate_limiter

sse = SseServerTransport("/messages")


class MCPServerApp:
    """ASGI application that handles MCP SSE endpoints directly.

    SSE endpoints are handled at the ASGI level to avoid conflicts with
    Starlette's response handling. Non-SSE requests are forwarded to
    a Starlette app for routing.
    """

    def __init__(self) -> None:
        # Starlette app for non-SSE routes
        self._starlette = Starlette(
            routes=[
                Route("/health", endpoint=self._health),
            ]
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._starlette(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # Handle SSE endpoints directly (bypass Starlette routing)
        if path == "/sse" and method == "GET":
            await self._handle_sse(scope, receive, send)
            return

        if path == "/messages" and method == "POST":
            await self._handle_messages(scope, receive, send)
            return

        # Rate limit check for non-SSE endpoints
        client_id = self._get_client_id(scope)
        if not rate_limiter.allow(client_id):
            retry_after = rate_limiter.get_retry_after(client_id)
            logger.warning(f"Rate limit exceeded for {client_id}")
            response = JSONResponse(
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
            await response(scope, receive, send)
            return

        # Add rate limit headers to response
        remaining = rate_limiter.get_remaining(client_id)

        async def send_with_headers(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-ratelimit-remaining", str(remaining).encode()))
                headers.append((b"x-ratelimit-limit", b"100"))
                message = {**message, "headers": headers}
            await send(message)

        await self._starlette(scope, receive, send_with_headers)

    async def _handle_sse(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle SSE connection for MCP."""
        async with sse.connect_sse(scope, receive, send) as streams:
            await mcp_app.run(streams[0], streams[1], mcp_app.create_initialization_options())

    async def _handle_messages(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle POST messages for MCP."""
        await sse.handle_post_message(scope, receive, send)

    async def _health(self, request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({"status": "ok"})

    def _get_client_id(self, scope: Scope) -> str:
        """Extract client identifier from request scope."""
        headers = dict(scope.get("headers", []))

        # Check for API key header first
        api_key = headers.get(b"x-api-key", b"").decode()
        if api_key:
            return f"api:{api_key[:8]}"

        # Fall back to IP address
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client = scope.get("client")
        client_host = client[0] if client else "unknown"
        return f"ip:{client_host}"


app = MCPServerApp()


def main() -> None:
    """Run the MCP HTTP server."""
    config = get_config()
    uvicorn.run(
        app,  # type: ignore[arg-type]
        host=config.mcp.server_host,
        port=config.mcp.server_port,
        log_level="info" if not config.mcp.debug else "debug",
    )


if __name__ == "__main__":
    main()
