from asyncio import Lock, TaskGroup
from datetime import timedelta
from typing import Callable, Dict, Optional

from anyio import create_task_group
from mcp import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    get_default_environment,
    stdio_client
)

from mcp.client.sse import (
    sse_client
)

from flock.core.context.context import FlockContext
from flock.core.flock_registry import FlockRegistry
from flock.core.mcp.mcp_session import MCPServerConnection
from flock.core.mcp.mcp_types import InitHookCallable
from flock.core.mcp.mcp_utils import _manage_server_session
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from flock.core.mcp.mcp_settings import MCPAuthenticationSettings
from flock.core.logging.logging import get_logger


class MCPConnection():
    """
    Description:
      Manages multiple MCP-Server connections.
    """

    def __init__(self, flock_registry: FlockRegistry, context: Optional[FlockContext] = None):
        super().__init__(context=context)
        self.flock_registry = flock_registry
        self.running_servers: Dict[str, MCPServerConnection] = {}
        self._lock = Lock()

        self._local_task_group: TaskGroup = None
        self._local_task_group_active: bool = False

    async def _close_all(self) -> None:
        """
        Disconnect from all servers.
        """
        servers_to_shut_down: list[tuple[str, MCPServerConnection]] = []

        async with self._lock:
            if not self.running_servers:
                return

            servers_to_shut_down = list(self.running_servers.items())

            self.running_servers.clear()

        for server_name, mcp_session in servers_to_shut_down:
            # TODO: logging
            mcp_session.request_shutdown()

    async def launch_server(
        self,
        server_name: str,
        client_session_factory: Callable[
            [MemoryObjectReceiveStream, MemoryObjectSendStream, timedelta | None],
            ClientSession
        ],
        init_hook: Optional[
            Callable[
            [ClientSession | None, MCPAuthenticationSettings | None],
            bool
            ]
        ]
    ) -> MCPServerConnection:
        """
        Description:
          Connect to a specific server and return a MCPSession connection.
        """
        if not self._local_task_group_active:
            self._local_task_group = create_task_group()
            await self._local_task_group.__aenter__()
            self._local_task_group_active = True
            self._tg = self._local_task_group
            # TODO: logging

        config = self.flock_registry.get_server(server_name)
        if not config:
            raise ValueError(f"Server '{server_name}' not found in registry.")

        def transport_context_factory():
            if config.transport_type == "stdio":
                server_params: StdioServerParameters = StdioServerParameters(
                    command=config.command,
                    args=config.args if config.args is not None else [],
                    env={**get_default_environment(), **(config.env or {})}
                )

                error_handler = get_logger(server_name)
                return stdio_client(server=server_params, errlog=error_handler)
            elif config.transport_type == "sse":
                return sse_client(
                    config.url,
                    config.additional_headers,
                    sse_read_timeout=config.read_transport_sse_timeout_millis * 1000
                )
            elif config.transport_type == "websockets":
                from mcp.client.websocket import websocket_client
                return websocket_client(
                    url=config.url,
                )
            else:
                raise ValueError(
                    f"Unknown Transport type: {config.transport_type}. Valid values are: `stdio`, `sse`, `websockets`")
        server_connection: MCPServerConnection = MCPServerConnection(
            server_name=server_name,
            server_connection=config,
            transport_context_factory=transport_context_factory,
            client_session_factory=client_session_factory,
            init_hook=init_hook or self.flock_registry.get_mcp_init_hook(
                server_name)
        )

        async with self._lock:
            if server_name in self.running_servers:
                return self.running_servers[server_name]

            self.running_servers[server_name] = server_connection
            self._local_task_group._tasks.start_soon(
                _manage_server_session, server_connection)

        # TODO: logging
        return server_connection

    async def get_server(
        self,
        server_name: str,
        client_session_factory: Callable[
            [MemoryObjectReceiveStream, MemoryObjectSendStream, timedelta | None],
            ClientSession
        ],
        init_hook: Optional["InitHookCallable"] = None
    ) -> MCPServerConnection:
        """
        Description:
          Get an instance of an active server connection.
          Launches local servers if they are not running.
        """

        async with self._lock:
            server_connection = self.running_servers.get(server_name)
            if server_connection and server_connection.is_healthy():
                return server_connection

            if server_connection:
                # TODO: logging
                self.running_servers.pop(server_name)
                server_connection.request_shutdown()

    async def __aenter__(self) -> "MCPConnection":
        self._local_task_group = create_task_group()
        await self._local_task_group.__aenter__()
        self._local_task_group_active = True
        self._tg = self._local_task_group
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Make sure that all connections are closed before exiting
        """
        try:
            await self._close_all()

        except Exception as ex:
            # TODO: Logging, error handling
            raise ex
