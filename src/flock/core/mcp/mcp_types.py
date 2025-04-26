from typing import Callable

from mcp import ClientSession

from flock.core.mcp.mcp_settings import MCPAuthenticationSettings


InitHookCallable = Callable[
    [
        ClientSession | None,
        MCPAuthenticationSettings | None
    ],
    bool
]
