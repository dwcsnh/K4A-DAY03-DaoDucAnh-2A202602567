"""
Minimal MCP server wrapper for the Roadmap Agent resource tools.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from tools import TOOLS_SCHEMA, dispatch_tool_call


class MCPRoadmapServer:
    def __init__(self, server_name: str = "roadmap-resource-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        raw_result = dispatch_tool_call(tool_name, arguments)
        content = json.loads(raw_result)
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content,
        }


# Backward-compatible alias for older imports.
MCPAcademicServer = MCPRoadmapServer


if __name__ == "__main__":
    server = MCPRoadmapServer()
    print(f"Server: {server.server_name} ({server.version})")
    print(f"Tools: {[tool['name'] for tool in server.list_tools()]}")
    print(
        json.dumps(
            server.call_tool(
                "search_resources",
                {
                    "query": "AWS IAM fundamentals",
                    "topic": "AWS",
                    "level": "BEGINNER",
                    "max_results": 2,
                },
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
