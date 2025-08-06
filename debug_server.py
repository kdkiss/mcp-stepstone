#!/usr/bin/env python3
"""
Debug version of Stepstone MCP Server
"""

import asyncio
import logging
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import mcp.types as types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug-server")

server = Server("stepstone-debug")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_jobs",
            description="Debug job search",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_terms": {"type": "array", "items": {"type": "string"}},
                    "zip_code": {"type": "string"},
                    "radius": {"type": "integer"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"Debug tool called: {name} with args: {arguments}")
    
    if name == "search_jobs":
        return [types.TextContent(
            type="text",
            text="Debug response: Tool is working correctly"
        )]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    options = InitializationOptions(
        server_name="stepstone-debug",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

if __name__ == "__main__":
    asyncio.run(main())