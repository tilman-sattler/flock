import asyncio 
from errno import ENOENT
import os
import sys 
import subprocess
import platform


from typing import Literal, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, InitializeResult, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from pydantic import Field

from flock.core.exception.flock_configuration_exception import FlockConfigurationException
from flock.core.mcp.client.mcp_client import MCPClient, MCPClientConfiguration
from flock.core.serialization.serializable import Serializable
from flock.core.logging.logging import get_logger


logger = get_logger("mcp.client.local")

class LocalMCPClientConfiguration(MCPClientConfiguration):
  """Configuration for a MCP Client communicating with a local MCP Server"""
  
  server_script_path: str = Field(
    description="Path to a JavaScript or Python script file which executes a local MCP Server"
  )
  
  interpreter: Literal["python", "node", "bun", "deno", "native"] = Field(
    description="The interpreter to use when executing a script for a MCP Server locally. `native` indicates that the script has been compiled into a native binary. (For example with `bun --compile --bytecode ./script.js`)"
  )
  
  server_script_arguments: list[str] = Field(
    default=[""],
    description="List of Flags for the server script executable."
  )
  
  server_env: dict[str, str] | None = Field(
    default=None,
    description="(optional) The environment to use for the server. If omitted, the default env of the host is used."
  )

class LocalMCPClient(MCPClient):
  """
  Description:
    A Client for Communicating with a local MCP Server Script
  """
  configuration: LocalMCPClientConfiguration = Field(
    description="Configuration for the Client."
  )
  
  session: Optional[ClientSession] = Field(
    exclude=True,
    description="The client session for the MCP-Client."
  )
  
  exit_stack: AsyncExitStack = Field(
    exclude=True,
    description="Async context manager."
  )
  
  server_params: StdioServerParameters = Field(
    exclude=True,
    description="Paramters for connection."
  )

  
  def __init__(self, config: LocalMCPClientConfiguration):
    super().__init__(config)
    self.session = None
    self.exit_stack = AsyncExitStack()
    self.server_params = LocalMCPClient._try_setup_local_server_config(config)
      
  
  async def _connect(self):
    """
    Description:
      Connect to a local MCP Server
    """
    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(
      self.server_params
    ))
    stdio, write = stdio_transport # destructure into separate streams
    session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
    
  
  async def _try_initialize_connection(self, session: ClientSession):
    """
    Description:
      
    """
    
  
  
  
  @staticmethod
  def _try_setup_local_server_config(config: LocalMCPClientConfiguration) -> StdioServerParameters:
    """
    Description:
      Gets the script specified in self.configuration.server_script_path
      ready for execution by finding either the appropriate "python" executable
      or "node" executable on the system and setting it up to run.
      If the required tools are not found on the system, then it will throw 
      an Exception.
    """
    
    is_python = config.server_script_path.endswith('.py')
    is_javascript = config.server_script_path.endswith('.js')
    
    is_native = config.interpreter == "native"
    
    
    if not (is_python or is_javascript) and not is_native:
      ex = FlockConfigurationException(f"{config.server_script_path} must have the .py or .js ending or be a native executable.")
      logger.exception(ex.message)
      raise ex
    
    command = "python" if is_python else config.interpreter
    
    if command == "native":
      command = os.path.abspath(config.server_script_path) # have it point to the executable itself.
      return StdioServerParameters(
        command=command,
        args=config.server_script_arguments,
        env=config.server_env
      )
    
    full_path_to_script = os.path.abspath(config.server_script_path)
    full_path_to_command = os.path.abspath(LocalMCPClient._find_tool_executable_on_system(command))
    args = [full_path_to_script] + config.server_script_arguments
    return StdioServerParameters(
      command=full_path_to_command,
      args=args,
      env=config.server_env
    )
    
  @staticmethod    
  def _find_currently_running_python_interpreter() -> str:
    """
    Description:
      Localizes the currently running python interpreter.
      
    Reason: 
      We are going to use the currently used Python
      Interpreter to execute Python MCP-Server Scripts.
      This is done for simplicity, as we can reasonably assume
      that wherever flock is running, a python interpreter is present.
      
    Returns:
      path (str): The fully qualified path to the currently used interpreter.
    """
    return sys.executable
  
  @staticmethod
  def _is_tool_present(name: Literal["node", "bun", "deno", "python"]) -> bool:
    """
    Description:
      Check if the given name executes a tool on the host system.
    Returns:
      bool -> True if executable exists on the host system, False otherwise
    """
    try:
      devnull = open(os.devnull)
      popen_instance: subprocess.Popen = subprocess.Popen([name], stdout=devnull, stderr=devnull)
      popen_instance.communicate()
      popen_instance.kill()
      
    except OSError as e:
      if e.errno == ENOENT: # File is not present
        logger.exception(f"No such file or directory: {name}")
        return False
      
    return True

  @staticmethod
  def _find_tool_executable_on_system(exec: Literal["node", "bun", "deno", "python"]) -> str:
    """
    Description:
      Tries to find the fully qualified path to the given executable on
      the host system.
    Returns:
      path (str): the fully qualified path to the specified executable.
    """
    if exec == "python":
      return LocalMCPClient._find_currently_running_python_interpreter()
    
    if LocalMCPClient._is_tool_present(exec):
      cmd = "where" if platform.system() == "Windows" else "which"
      return subprocess.call([cmd, exec])
    else:
      ex = FlockConfigurationException(f"The requested executable: {exec} is not present.")
      logger.exception(ex.message)
      raise ex