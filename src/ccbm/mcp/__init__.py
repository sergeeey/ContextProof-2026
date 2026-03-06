"""
MCP — Model Context Protocol для CCBM.

Интеграция с AI-агентами через стандартный протокол.
"""

from .server import (
    ccbm_server,
    main,
    list_tools,
    call_tool,
    list_resources,
    read_resource,
)

__all__ = [
    "ccbm_server",
    "main",
    "list_tools",
    "call_tool",
    "list_resources",
    "read_resource",
]
