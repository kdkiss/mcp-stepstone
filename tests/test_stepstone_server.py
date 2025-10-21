import asyncio
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

import stepstone_server


def test_search_jobs_no_results(monkeypatch, caplog):
    search_terms = ["term1", "term2"]

    def fake_search_jobs(terms, zip_code, radius):
        assert terms == search_terms
        return {term: [] for term in terms}

    def fake_create_session(results, *args, **kwargs):
        assert results == []
        return "test-session"

    monkeypatch.setattr(stepstone_server.scraper, "search_jobs", fake_search_jobs)
    monkeypatch.setattr(stepstone_server.session_manager, "create_session", fake_create_session)

    with caplog.at_level("INFO"):
        response = asyncio.run(
            stepstone_server.handle_call_tool(
                "search_jobs",
                {"search_terms": search_terms, "zip_code": "40210", "radius": 5},
            )
        )

    assert response
    message = response[0].text

    assert "Total Jobs Found: 0" in message
    assert "No jobs found for this search term." in message
    assert "Try refining your search terms or expanding the radius." in message

    assert any("returned no results" in record.getMessage() for record in caplog.records)


def test_search_jobs_invalid_terms(monkeypatch, caplog):
    def fake_search_jobs(*args, **kwargs):
        pytest.fail("search_jobs should not be invoked when validation fails")

    def fake_create_session(*args, **kwargs):
        pytest.fail("create_session should not be invoked when validation fails")

    monkeypatch.setattr(stepstone_server.scraper, "search_jobs", fake_search_jobs)
    monkeypatch.setattr(
        stepstone_server.session_manager, "create_session", fake_create_session
    )

    with caplog.at_level("WARNING"):
        response = asyncio.run(
            stepstone_server.handle_call_tool(
                "search_jobs",
                {"search_terms": [" ", 123], "zip_code": "40210", "radius": 5},
            )
        )

    assert response
    message = response[0].text
    assert (
        message
        == "Error: search_terms must contain at least one non-empty string"
    )
    logged_messages = [record.getMessage() for record in caplog.records]
    assert any("Ignoring non-string search term" in msg for msg in logged_messages)
    assert any("Ignoring empty search term entry" in msg for msg in logged_messages)


_SERVER_SCRIPT = Path(__file__).resolve().parents[1] / "stepstone_server.py"


def _start_server():
    return subprocess.Popen(
        [sys.executable, str(_SERVER_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _send_content_length(proc, message):
    payload = json.dumps(message).encode('utf-8')
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode('ascii')
    proc.stdin.write(header + payload)
    proc.stdin.flush()


def _read_content_length_response(stream, timeout=5):
    fd = stream.fileno()
    buffer = b''
    deadline = time.time() + timeout

    while time.time() < deadline:
        header_end = buffer.find(b"\r\n\r\n")
        separator = 4
        if header_end == -1:
            header_end = buffer.find(b"\n\n")
            separator = 2
        if header_end != -1:
            break

        remaining = deadline - time.time()
        if remaining <= 0:
            break
        ready, _, _ = select.select([fd], [], [], remaining)
        if not ready:
            continue
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        buffer += chunk

    assert header_end != -1, 'did not receive Content-Length header'
    header_block = buffer[:header_end]
    content_length = None
    for line in header_block.splitlines():
        if b":" not in line:
            continue
        name, value = line.split(b":", 1)
        if name.strip().lower() == b'content-length':
            content_length = int(value.strip())
            break

    assert content_length is not None, 'Content-Length missing in response'
    total_length = header_end + separator + content_length
    while len(buffer) < total_length:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        ready, _, _ = select.select([fd], [], [], remaining)
        if not ready:
            continue
        chunk = os.read(fd, total_length - len(buffer))
        if not chunk:
            break
        buffer += chunk

    body = buffer[header_end + separator : total_length]
    return body


@pytest.mark.skipif(sys.platform == 'win32', reason='select behaviour differs on Windows')
def test_initialize_supports_content_length():
    proc = _start_server()
    try:
        _send_content_length(
            proc,
            {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2025-06-18',
                    'capabilities': {},
                    'clientInfo': {'name': 'pytest', 'version': '0.0.0'},
                },
            },
        )

        body = _read_content_length_response(proc.stdout)
        response = json.loads(body.decode('utf-8'))
        assert response['id'] == 1
        assert response['result']['protocolVersion']
    finally:
        proc.kill()
        proc.communicate(timeout=1)


@pytest.mark.skipif(sys.platform == 'win32', reason='select behaviour differs on Windows')
def test_initialize_supports_newline_delimited_json():
    proc = _start_server()
    try:
        message = json.dumps(
            {
                'jsonrpc': '2.0',
                'id': 2,
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2025-06-18',
                    'capabilities': {},
                    'clientInfo': {'name': 'pytest', 'version': '0.0.0'},
                },
            }
        ).encode('utf-8')
        proc.stdin.write(message + b"\n")
        proc.stdin.flush()

        fd = proc.stdout.fileno()
        buffer = b''
        deadline = time.time() + 5
        while time.time() < deadline:
            newline_index = buffer.find(b"\n")
            if newline_index != -1:
                line = buffer[:newline_index].strip()
                response = json.loads(line.decode('utf-8'))
                assert response['id'] == 2
                assert 'result' in response
                break

            remaining = deadline - time.time()
            if remaining <= 0:
                break
            ready, _, _ = select.select([fd], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            buffer += chunk
        else:
            pytest.fail('newline framed response not received')
    finally:
        proc.kill()
        proc.communicate(timeout=1)
