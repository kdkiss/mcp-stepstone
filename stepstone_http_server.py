"""HTTP transport wrapper for the Stepstone MCP server.

This module exposes a Starlette application that proxies HTTP traffic to the
existing STDIO-based MCP server implementation. The adapter enables browsers or
remote clients to communicate with the server while satisfying CORS
requirements enforced by hosted MCP environments.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

import stepstone_server

logger = logging.getLogger("stepstone-http-server")


def _cors_headers() -> list[tuple[bytes, bytes]]:
    """Headers applied to every HTTP response."""
    return [
        (b"access-control-allow-origin", b"*"),
        (b"access-control-allow-methods", b"GET,POST,DELETE,OPTIONS"),
        (b"access-control-allow-headers", b"*"),
        (b"access-control-expose-headers", b"mcp-session-id"),
    ]


def _cors_preflight_headers() -> list[tuple[bytes, bytes]]:
    """Headers returned for CORS preflight responses."""
    headers = list(_cors_headers())
    headers.append((b"access-control-max-age", b"86400"))
    return headers


def _merge_headers(
    existing: list[tuple[bytes, bytes]], additions: list[tuple[bytes, bytes]]
) -> list[tuple[bytes, bytes]]:
    """Merge HTTP headers while overriding duplicates using case-insensitive keys."""

    header_map: dict[bytes, tuple[bytes, bytes]] = {
        key.lower(): (key, value) for key, value in existing
    }
    for key, value in additions:
        header_map[key.lower()] = (key, value)
    return list(header_map.values())



def create_app() -> Starlette:
    """Create a Starlette application exposing the MCP server over HTTP."""

    session_manager = StreamableHTTPSessionManager(
        stepstone_server.server,
        json_response=False,
        stateless=False,
    )

    async def streamable_http_endpoint(scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            raise RuntimeError("Unsupported ASGI scope type")

        method = scope.get("method", "GET").upper()
        if method == "OPTIONS":
            logger.debug("Handling CORS preflight for %s", scope.get("path"))
            await send(
                {
                    "type": "http.response.start",
                    "status": 204,
                    "headers": _cors_preflight_headers(),
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                message["headers"] = _merge_headers(headers, _cors_headers())
            await send(message)

        await session_manager.handle_request(scope, receive, send_with_cors)

    async def homepage(request: Request):
        response = JSONResponse(
            {
                "status": "ok",
                "message": "Stepstone MCP HTTP endpoint",
                "endpoints": {"mcp": "/mcp"},
            }
        )
        for key, value in _cors_headers():
            response.headers[key.decode("ascii")] = value.decode("ascii")
        return response

    @asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            yield

    routes = [
        Route("/", homepage, methods=["GET"]),
        Mount("/mcp", app=streamable_http_endpoint),
    ]

    return Starlette(routes=routes, lifespan=lifespan)


app = create_app()


def main() -> None:
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info("Starting Stepstone MCP HTTP server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level=os.environ.get("LOG_LEVEL", "info"))


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    main()
