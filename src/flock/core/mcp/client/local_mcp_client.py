import asyncio 
from errno import ENOENT
import os
import sys 
import subprocess
import platform


from typing import Literal, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from pydantic import Field

from flock.core.exception.flock_configuration_exception import FlockConfigurationException
from flock.core.serialization.serializable import Serializable
from flock.modules.mcp.client.mcp_client import MCPClient, MCPClientConfiguration
from flock.core.logging.logging import get_logger


logger = get_logger("mcp.client.local")

class LocalMCPClientConfiguration(MCPClientConfiguration):
  """Configuration for a MCP Client communicating with a local MCP Server"""
  
  server_script_path: str | None = Field(
    default=None,
    description="Path to a JavaScript or Python script file which executes a local MCP Server"
  )

class LocalMCPClient(MCPClient):
  """
  Description:
    A Client for Communicating with a local MCP Server Script
  """
  configuration: LocalMCPClientConfiguration = Field(
    description="Configuration for the Client"
  )
  
  def __init__(self, mcpClientConfiguration: LocalMCPClientConfiguration):
    super().__init__(mcpClientConfiguration)
      
  
  async def _connect(self):
    """
    Description:
      Connect to a local MCP Server
    """
    pass
  
  
  
  
  def _try_set_up_executable(self):
    """
    Description:
      Gets the script specified in self.configuration.server_script_path
      ready for execution by finding either the appropriate "python" executable
      or "node" executable on the system and setting it up to run.
      If the required tools are not found on the system, then it will throw 
      an Exception.
    """
    is_python = self.configuration.server_script_path.endswith('.py')
    is_javascript = self.configuration.server_script_path.endswith('.js')
    
    
    if not (is_python or is_javascript):
      ex = FlockConfigurationException(f"{self.configuration.server_script_path} must have the .py or .js ending")
      logger.exception(ex.message)
      raise ex
    
  def _find_currently_running_python_interpreter(self) -> str:
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
  
  def _is_present(self, name: Literal["node", "bun", "deno", "python"]) -> bool:
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
        return False
      
    return True

  def _find_tool_executable_on_system(self, exec: Literal["node", "bun", "deno", "python"]) -> str:
    """
    Description:
      Tries to find the fully qualified path to the given executable on
      the host system.
    """
    if exec == "python":
      return self._find_currently_running_python_interpreter()
    
    if self._is_present(exec):
      cmd = "where" if platform.system() == "Windows" else "which"
      return subprocess.call([cmd, exec])