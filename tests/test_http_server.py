from starlette.testclient import TestClient

import stepstone_http_server


def test_cors_preflight_allows_any_origin():
    app = stepstone_http_server.create_app()

    with TestClient(app) as client:
        response = client.options(
            "/mcp",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == "*"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "*"


def test_homepage_reports_status():
    app = stepstone_http_server.create_app()

    with TestClient(app) as client:
        response = client.get("/", headers={"Origin": "https://foo"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["endpoints"]["mcp"] == "/mcp"
    assert response.headers["access-control-allow-origin"] == "*"


def test_mcp_session_header_is_exposed():
    app = stepstone_http_server.create_app()

    with TestClient(app) as client:
        response = client.post(
            "/mcp/",
            headers={"Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": "noop", "method": "ping"},
        )

    assert response.headers["access-control-expose-headers"] == "mcp-session-id"
    assert "mcp-session-id" in response.headers


def test_initialize_without_accept_header_succeeds():
    app = stepstone_http_server.create_app()

    payload = {
        "jsonrpc": "2.0",
        "id": 123,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0.0.0"},
        },
    }

    with TestClient(app) as client:
        response = client.post("/mcp", json=payload)

    assert response.status_code == 200
    assert response.headers["mcp-session-id"]
    assert response.headers["content-type"].startswith("text/event-stream")
