

from asyncio import Event
from datetime import timedelta
from typing import AsyncGenerator, Callable, Literal, Optional
from mcp import ClientSession
from mcp.types import JSONRPCMessage, ServerCapabilities
from pydantic import BaseModel, Field
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from flock.core.mcp.mcp_settings import MCPAuthenticationSettings, MCPClientSettings, MCPServerConnection


class MCPServerConnection(BaseModel):

    client_session: ClientSession | None = Field(
        default=None,
        description="Active Client Session. A connection to a server."
    )

    type: Literal["local", "remote"] = Field(
        description="What kind of Server the session is connected to."
    )

    server_name: str = Field(
        description="The name of the server this Session is connected to."
    )

    connection_settings: MCPServerConnection = Field(
        description="Settings for the connection."
    )

    _client_session_factory: Optional[
        Callable[
            [MemoryObjectReceiveStream, MemoryObjectSendStream, timedelta | None],
            ClientSession
        ]
    ] = Field(
        default=None,
        description="Factory for creating a client."
    )

    _init_hook: Optional[
        Callable[
            [ClientSession | None, MCPAuthenticationSettings | None],
            bool
        ]
    ] = Field(
        default=None,
        description="Init Hook."
    )

    _transport_context_factory: Optional[
        Callable[
            [],
            AsyncGenerator[
                tuple[
                    MemoryObjectReceiveStream[JSONRPCMessage] | Exception,
                    MemoryObjectSendStream[JSONRPCMessage]
                ],
                None
            ]
        ]
    ] = Field(
        default=None,
        description="Transport Context Factory."
    )

    _initialize_event: Event = Field(
        default=Event(),
        description="Signal that session is fully up and initialized."
    )

    _shutdown_event: Event = Field(
        default=Event(),
        description="Signal that session should be terminated."
    )

    _error_occurred: bool = Field(
        default=False,
        exclude=True,
        description="If an error occurred."
    )

    _error_message: str | None = Field(
        default=None,
        exclude=True,
        description="Error Message"
    )

    _server_capabilities: ServerCapabilities | None = Field(
        default=None,
        exclude=True,
        description="Server Capabilities."
    )

    def is_healthy(self) -> bool:
        """
        Description:
          Check if the server connection is healthy and ready to use.
        """
        return self.client_session is not None and not self._error_occurred

    def reset_error_state(self) -> bool:
        """
        Description:
          Reset the error state, allowing for reconnection attempts.
        """
        self._error_occurred = False
        self._error_message = None

    def request_shutdown(self) -> None:
        """
        Description:
          Request the server to shut down.
          Signals the server lifecycle task to exit.
        """
        self._shutdown_event.set()

    async def wait_for_shutdown_request(self) -> None:
        """
        Description:
          Wait until the shutdown event is set.
        """
        await self._shutdown_event.wait()

    async def initialize_session(self) -> None:
        """
        Description:
          Initializes the server connection and session.
          Must be called within an async context.
        """

        result = await self.client_session.initialize()

        self._server_capabilities = result.capabilities
        # If there is an init hook set, then run it now.
        if self._init_hook:
            # TODO: logging
            self._init_hook(self.client_session,
                            self.connection_settings.authentication_settings)

        self._initialize_event.set()

    async def wait_for_initialization(self) -> None:
        """
        Description:
          Wait until the session is fully initialized.
        """
        await self._initialize_event.wait()

    def create_session(self, read_stream: MemoryObjectReceiveStream, write_stream: MemoryObjectSendStream) -> ClientSession:
        """
        Description:
          Create a new session instance for the server connection.
        """
        read_timeout = (
            timedelta(milliseconds=self.connection_settings.read_timeout_millis)
            if self.connection_settings.read_timeout_millis
            else None
        )

        session = self._client_session_factory(
            read_stream, write_stream, read_timeout)

        if hasattr(session, "server_config"):
            session.server_config = self.connection_settings

        self.client_session = session

        return session
