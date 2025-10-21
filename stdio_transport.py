"""Adaptive stdio transport that supports both newline and Content-Length framing."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import Literal

import anyio
from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from io import TextIOWrapper

import mcp.types as types
from mcp.shared.message import SessionMessage

FramingMode = Literal["newline", "content-length"]


@asynccontextmanager
async def adaptive_stdio_server():
    """Create a stdio transport that accepts both framing strategies."""

    stdin = anyio.wrap_file(TextIOWrapper(sys.stdin.buffer, encoding="utf-8"))
    stdout = anyio.wrap_file(TextIOWrapper(sys.stdout.buffer, encoding="utf-8"))

    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    framing_mode: dict[str, FramingMode] = {}
    framing_event = anyio.Event()

    async def stdin_reader() -> None:
        async with read_stream_writer:
            async for line in stdin:
                payload: str | None = None

                if line.lower().startswith("content-length:"):
                    headers = [line]
                    content_length: int | None = None

                    while True:
                        next_line = await stdin.readline()
                        if next_line in ("", "\n", "\r\n"):
                            break
                        headers.append(next_line)

                    for header_line in headers:
                        if ":" not in header_line:
                            continue
                        name, value = header_line.split(":", 1)
                        if name.strip().lower() == "content-length":
                            try:
                                content_length = int(value.strip())
                            except ValueError:  # pragma: no cover - invalid header value
                                content_length = None
                            break

                    if content_length is None:
                        await read_stream_writer.send(ValueError("Missing Content-Length header"))
                        continue

                    remaining = content_length
                    chunks: list[str] = []
                    while remaining > 0:
                        chunk = await stdin.read(remaining)
                        if chunk == "":  # EOF before full body
                            break
                        chunks.append(chunk)
                        remaining -= len(chunk)

                    body = "".join(chunks)
                    if len(body) != content_length:
                        await read_stream_writer.send(ValueError("Incomplete Content-Length body"))
                        continue

                    payload = body
                    if not framing_event.is_set():
                        framing_mode["value"] = "content-length"
                        framing_event.set()
                else:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    payload = stripped
                    if not framing_event.is_set():
                        framing_mode["value"] = "newline"
                        framing_event.set()

                try:
                    message = types.JSONRPCMessage.model_validate_json(payload)
                except Exception as exc:  # pragma: no cover - invalid payload
                    await read_stream_writer.send(exc)
                    continue

                await read_stream_writer.send(SessionMessage(message))

    async def stdout_writer() -> None:
        async with write_stream_reader:
            async for session_message in write_stream_reader:
                message_json = session_message.message.model_dump_json(
                    by_alias=True, exclude_none=True
                )

                if not framing_event.is_set():
                    framing_mode["value"] = "content-length"
                    framing_event.set()

                mode = framing_mode.get("value", "content-length")

                try:
                    if mode == "content-length":
                        header = f"Content-Length: {len(message_json.encode('utf-8'))}\r\n\r\n"
                        await stdout.write(header + message_json)
                    else:
                        await stdout.write(message_json + "\n")
                    await stdout.flush()
                except anyio.ClosedResourceError:  # pragma: no cover - closed pipe
                    break

    async with anyio.create_task_group() as tg:
        tg.start_soon(stdin_reader)
        tg.start_soon(stdout_writer)
        yield read_stream, write_stream
