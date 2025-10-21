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
from starlette.routing import Route
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



def _update_accept_header(headers: list[tuple[bytes, bytes]]) -> None:
    """Ensure the Accept header allows both JSON and SSE responses."""

    required_types = ("application/json", "text/event-stream")
    header_index = next(
        (idx for idx, (name, _) in enumerate(headers) if name.lower() == b"accept"),
        None,
    )

    if header_index is None:
        headers.append((b"accept", b", ".join(value.encode("latin-1") for value in required_types)))
        return

    name, value = headers[header_index]
    media_types = [token.strip() for token in value.decode("latin-1").split(",") if token.strip()]

    def satisfies(token: str, target: str) -> bool:
        base = token.split(";", 1)[0].strip()
        if base == "*/*":
            return False
        if base.endswith("/*"):
            prefix = base.split("/", 1)[0]
            return target.startswith(f"{prefix}/")
        return base == target

    updated = False
    for required in required_types:
        if not any(satisfies(token, required) for token in media_types):
            media_types.append(required)
            updated = True

    if updated:
        new_value = ", ".join(media_types).encode("latin-1")
        headers[header_index] = (name, new_value)


def _ensure_required_headers(scope: Scope) -> Scope:
    """Return a scope copy with Accept and Content-Type headers normalised."""

    headers = list(scope.get("headers", []))
    headers = [(name, value) for name, value in headers]

    _update_accept_header(headers)

    method = scope.get("method", "").upper()
    has_content_type = any(name.lower() == b"content-type" for name, _ in headers)
    if method == "POST" and not has_content_type:
        headers.append((b"content-type", b"application/json"))

    updated_scope = dict(scope)
    updated_scope["headers"] = headers
    return updated_scope


def create_app() -> Starlette:
    """Create a Starlette application exposing the MCP server over HTTP."""

    session_manager = StreamableHTTPSessionManager(
        stepstone_server.server,
        json_response=False,
        stateless=False,
    )

    class StreamableEndpoint:
        def __init__(self, manager: StreamableHTTPSessionManager):
            self._manager = manager

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
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

            normalized_scope = _ensure_required_headers(scope)
            await self._manager.handle_request(normalized_scope, receive, send_with_cors)

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

    streamable_endpoint = StreamableEndpoint(session_manager)

    routes = [
        Route("/", homepage, methods=["GET"]),
        Route("/mcp", streamable_endpoint, methods=["GET", "POST", "DELETE", "OPTIONS"]),
        Route("/mcp/", streamable_endpoint, methods=["GET", "POST", "DELETE", "OPTIONS"]),
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
