

import asyncio
from contextlib import AsyncExitStack
import itertools
import os
from types import TracebackType
from typing import List, Optional, Literal, Tuple, cast

import concurrent
from mcp import ClientSession, InitializeResult, ListPromptsResult, ListToolsResult, StdioServerParameters
from mcp.types import PromptArgument, Prompt, PromptMessage
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.websocket import websocket_client
from pydantic import ConfigDict
from flock.core.mcp.mcp_prompt import MCPPrompt
from flock.core.mcp.mcp_tool import MCPTool
from flock.core.serialization.serializable import Serializable
from flock.core.mcp.mcp_connections import *
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
  
  tools: dict[str, MCPTool] = Field(
    exclude=True,
    description="A dict containing all tools available through the clients in the client."
  )
  
  prompts: dict[str, MCPPrompt] = Field(
    exclude=True,
    description="A dict containing all prompts available through the clients in the client."
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
  
  async def _connect_to_server_async(self, server_name: str, transport: Literal["stdio", "sse", "websocket"], **kwargs) -> ClientSession:
    if transport == "sse":
      if "url" not in kwargs:
        raise FlockConfigurationException("'url' parameter is required for SSE connection.")
      else:
        result = await self._connect_to_server_via_sse_async(server_name=server_name, url=kwargs["url"], headers=kwargs["headers"])
        return result
    elif transport == "stdio":
      if "command" not in kwargs:
        raise FlockConfigurationException("'command' parameter is required for STDIO connection.")
      if "args" not in kwargs:
        raise FlockConfigurationException("'args' parameter is required for STDIO connection.")
      result = await self._connect_to_server_via_stdio_async(
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
      result = await self._connect_to_server_via_websockets_async(
        server_name=server_name,
        url=kwargs["url"],
        session_kwargs=kwargs.get("session_kwargs"),
      )
      return result
    else:
      raise FlockConfigurationException(f"Transport: {transport} is not supported. Valid options are: 'sse', 'stdio', 'websocket', 'custom'.")
  
  async def _connect_to_server_via_websockets_async(self, server_name: str, url: str | Url, session_kwargs: dict[str, Any] | None = None) -> ClientSession:
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
    
    return await self._initialize_session_async(server_name=server_name, session=session)
  
  async def _connect_to_server_via_sse_async(self, server_name: str, url: str, headers: dict[str, Any] | None = None, timeout: int = DEFAULT_HTTP_TIMEOUT, sse_read_timeout: int = DEFAULT_SSE_READ_TIMEOUT, session_kwargs: dict[str, Any] | None = None) -> ClientSession:
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
    
    return await self._initialize_session_async(server_name=server_name, session=session)
  
  async def _connect_to_server_via_stdio_async(self, server_name: str, command: str, args: list[str], env: dict[str, str] | None = None, encoding: Literal["ascii", "utf-8", "utf-16", "utf-32"] = "utf-8", encoding_error_handler: Literal["strict", "ignore", "replace"] = "strict", session_kwargs: dict[str, Any] | None = None) -> ClientSession:
    
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
    return await self._initialize_session_async(server_name=server_name, session=session)
    
  async def _initialize_session_async(self, server_name: str, session: ClientSession) -> ClientSession:
    result: InitializeResult = await session.initialize()
    self.sessions[server_name] = session
    return session
  
  async def _retrieve_prompts_from_server_async(self, client_session: ClientSession) -> tuple[ClientSession, ListPromptsResult]:
    prompts: ListPromptsResult = await client_session.list_prompts()
    return (client_session, prompts)
  
  async def _convert_mcp_prompts_to_flock_prompts_async(self, client_sessions: dict[str, ClientSession]) -> List[MCPTool]:
    
    # Each task represents an API call to a client session
    tasks = [
      asyncio.create_task(
        self._retrieve_prompts_from_server_async(client_session=session)
      ) for session in client_sessions.values()
    ]
    
    # Run all tasks concurrently and wait for them to finish
    results: List[Tuple[ClientSession, ListPromptsResult]] = await asyncio.gather(tasks)
    
    # Create Prompts concurrently
    conversion_tasks = [
      asyncio.create_task(
        self._process_prompts_async(
          session=session,
          prompts=prompts
        )
      ) for session, prompts in results
    ]
    
    conversion_results: List[List[MCPPrompt]] = await asyncio.gather(conversion_tasks)
    
    complete_prompt_list: List[MCPPrompt] = itertools.chain.from_iterable(conversion_results)
    
    return complete_prompt_list
    
  async def _process_prompts_async(self, session: ClientSession, prompts: List[Prompt]) -> List[MCPPrompt]:
    tasks = [
      asyncio.create_task(
        self._create_flock_prompt(
          session=session,
          prompt=prompt
        )
      ) for prompt in prompts
    ]
    results: List[MCPPrompt] = await asyncio.gather(tasks)
    
    return results
  
  def _create_flock_prompt(self, session: ClientSession, prompt: Prompt) -> MCPPrompt:
    return MCPPrompt(
      name=prompt.name,
      description=prompt.description,
      arguments=prompt.arguments,
      model_config=prompt.model_config,
    )
    
  async def _process_tools_async(self, session: ClientSession, list_promptsresult: ListPromptsResult) -> List[MCPPrompt]:
    tasks = [
      asyncio.create_task(
        self._create_flock_prompt(session=session, name=prompt.name)
      ) for prompt in list_promptsresult.prompts
    ]
  

    
  async def _retrieve_tools_from_server_async(self, client_session: ClientSession) -> tuple[ClientSession, ListToolsResult]:
    tools = await client_session.list_tools()
    return (client_session, tools)
  
  async def _convert_mcp_tools_to_flock_tools_async(self, client_sessions: dict[str, ClientSession]) -> List[MCPTool]:
    
    # Each task represents an API call to a client session
    tasks = [
      asyncio.create_task(self._retrieve_tools_from_server_async(session=session))
      for session in client_sessions.values()
    ]
    
    # Run all tasks concurrently and wait for them to finish
    results: List[tuple[ClientSession, ListToolsResult]] = await asyncio.gather(tasks)
    
    # Create tools concurrently
    conversion_tasks = [
      asyncio.create_task(
        self._process_tools_async(
          session=session,
          list_tools_result=list_tools_result,
        )
      ) for session, list_tools_result in results
    ]
    
    # Gather results
    converted_tools: List[List[MCPTool]] = await asyncio.gather(conversion_tasks)
    
    complete_tool_list: List[MCPTool] = itertools.chain.from_iterable(converted_tools)
    
    return complete_tool_list
  
  async def _process_tools_async(self, session: ClientSession, list_tools_result: ListToolsResult) -> List[MCPTool]:
    tasks = [
      asyncio.create_task(
        self._create_flock_tool(
          session=session,
          name=tool.name,
          description=tool.description,
          input_schema=tool.inputSchema,
          model_config=tool.model_config,
        )
      ) for tool in list_tools_result.tools
    ]
    
    return await asyncio.gather(tasks)
  
  def _create_flock_tool(self, session: ClientSession, name: str, description: str | None, input_schema: dict[str, Any], model_config: ConfigDict) -> MCPTool:
    return MCPTool(
      session=session,
      name=name,
      description=description,
      input_schema=input_schema,
      model_config=model_config
    )
  
  async def __aenter__(self) -> "MCPClient":
    """
    __aenter__() is called when entering an `async with`-block, performing setup operations before execution continues inside the block.
    It returns an Instance of the class for use inside the block.
    """
    try:
      servers: dict[str, FlockConnectionConfig] = self.servers or {}
      
      # Connect to servers in parallel
      tasks = [
        asyncio.create_task(
          self._connect_to_server_async(server_name=server_name, **connection)
        ) for server_name, connection in servers.items()
      ]
      results: List[ClientSession] = await asyncio.gather(tasks)
      
    except Exception:
      await self.exit_stack.aclose()
      raise
    
  async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: TracebackType | None
  ) -> None:
    """
    """
    await self.exit_stack.aclose()