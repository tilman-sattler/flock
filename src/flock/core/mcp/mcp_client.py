

from contextlib import AsyncExitStack
import os
from typing import Optional, Literal, cast

from mcp import ClientSession, InitializeResult, ListToolsResult, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.websocket import websocket_client
from flock.core.serialization.serializable import Serializable
from flock.core.mcp.connection import *
from flock.core.exception.flock_configuration_exception import FlockConfigurationException


DEFAULT_HTTP_TIMEOUT = 3_000
DEFAULT_SSE_READ_TIMEOUT = 3_000

class MCPClient(Serializable):
  
  servers: Optional[dict[str, FlockConnectionConfig]] = Field(
    default=None,
    description="A map containing all configured servers that this client handles."
  )
  
  sessions: dict[str, ClientSession] = Field(
    exclude=True,
    description="Holds the clientsessions for the different servers."
  )
  
  exit_stack: AsyncExitStack = Field(
    exclude=True,
    description="Async Exit Stack."
  )
  
  def __init__(self, servers: dict[str, FlockConnectionConfig]) -> None:
    """
    Description:
      Initialize the client.
    
    Args:
      servers:
    """
    super().__init__()
    self.servers = servers
    self.sessions = {}
    self.exit_stack = AsyncExitStack()
  
  async def _connect_to_server(self, server_name: str, transport: Literal["stdio", "sse", "websocket"], **kwargs) -> ClientSession:
    if transport == "sse":
      if "url" not in kwargs:
        raise FlockConfigurationException("'url' parameter is required for SSE connection.")
      else:
        result = await self._connect_to_server_via_sse(server_name=server_name, url=kwargs["url"], headers=kwargs["headers"])
        return result
    elif transport == "stdio":
      if "command" not in kwargs:
        raise FlockConfigurationException("'command' parameter is required for STDIO connection.")
      if "args" not in kwargs:
        raise FlockConfigurationException("'args' parameter is required for STDIO connection.")
      result = await self._connect_to_server_via_stdio(
        server_name=server_name,
        command=kwargs["command"],
        env=kwargs.get("env"),
        encoding=kwargs.get("encoding", "utf-8"),
        encoding_error_handler=kwargs.get(
          "encoding_error_handler",
          "strict"
        ),
        session_kwargs=kwargs.get("session_kwargs")
      )
      return result
    elif transport == "websocket":
      if "url" not in kwargs:
        raise FlockConfigurationException("'url' parameter is required for Websocket connection.")
      result = await self._connect_to_server_via_websockets(
        server_name=server_name,
        url=kwargs["url"],
        session_kwargs=kwargs.get("session_kwargs"),
      )
      return result
    else:
      raise FlockConfigurationException(f"Transport: {transport} is not supported. Valid options are: 'sse', 'stdio', 'websocket', 'custom'.")
  
  async def _connect_to_server_via_websockets(self, server_name: str, url: str | Url, session_kwargs: dict[str, Any] | None = None) -> ClientSession:
    try:
      from mcp.client.websocket import websocket_client
    except ImportError:
      raise ImportError(
        "Could not import Websocket Client.",
        "To use Websocket connections, please install the required dependency with:",
        "'pip install mcp[ws]' or 'pip install websockets'"
      )
    ws_transport = await self.exit_stack.enter_async_context(websocket_client(url))
    read, write = ws_transport
    session_kwargs = session_kwargs or {}
    session = cast(
      ClientSession,
      await self.exit_stack.enter_async_context(ClientSession(read, write, **session_kwargs))
    )
    
    return await self._initialize_session(server_name=server_name, session=session)
  
  async def _connect_to_server_via_sse(self, server_name: str, url: str, headers: dict[str, Any] | None = None, timeout: int = DEFAULT_HTTP_TIMEOUT, sse_read_timeout: int = DEFAULT_SSE_READ_TIMEOUT, session_kwargs: dict[str, Any] | None = None) -> ClientSession:
    # Create and store connection
    sse_transport = await self.exit_stack.enter_async_context(
      sse_client(url=url, headers=headers, timeout=timeout, sse_read_timeout=sse_read_timeout)
    )
    read, write = sse_transport
    session_kwargs = session_kwargs or {}
    session = cast(
      ClientSession,
      await self.exit_stack.enter_async_context(ClientSession(read, write, **session_kwargs)),
    )
    
    return await self._initialize_session(server_name=server_name, session=session)
  
  async def _connect_to_server_via_stdio(self, server_name: str, command: str, args: list[str], env: dict[str, str] | None = None, encoding: Literal["ascii", "utf-8", "utf-16", "utf-32"] = "utf-8", encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict", session_kwargs: dict[str, Any] | None = None) -> ClientSession:
    
    # Autmatically inject PATH into `env` value, if not already set.
    env = env or {}
    if "PATH" not in env:
      env["PATH"] = os.environ.get("PATH", "")
      
    server_params = StdioServerParameters(
      command=command,
      args=args,
      encoding=encoding,
      encoding_error_handler=encoding_error_handler
    )
    
    # Create and store connection
    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    read, write = stdio_transport
    session_kwargs = session_kwargs or {}
    session = cast(
      ClientSession,
      await self.exit_stack.enter_async_context(ClientSession(read, write, **session_kwargs))
    )
    return await self._initialize_session(server_name=server_name, session=session)
    
  async def _initialize_session(self, server_name: str, session: ClientSession) -> ClientSession:
    result: InitializeResult = await session.initialize()
    self.sessions[server_name] = session
    return session
    
  async def _load_tools_from_server(self, server_name: str) -> ListToolsResult:
    tools: ListToolsResult = self.sessions[server_name].list_tools()
    return tools