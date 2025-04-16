"""Module for handling Model-Context-Protocol Provided Tools"""

from typing import TYPE_CHECKING, Any

from pydantic import  Field

from flock.core.context.context_vars import FLOCK_BATCH_SILENT_MODE

if TYPE_CHECKING:
  from flock.core import FlockAgent
  
from flock.core.context.context import FlockContext
from flock.core.flock_module import FlockModule, FlockModuleConfig
from flock.core.logging.formatters.themed_formatter import (
  ThemedAgentResultFormatter,
)
from flock.core.logging.formatters.themes import OutputTheme
from flock.core.logging.logging import get_logger

logger = get_logger("module.mcp.tools")

class MCPToolsServerConfig():
  """Stores the configuration for a MCP-Server"""
  pass

class MCPToolsModuleConfig(FlockModuleConfig):
  """Configuration for MCP Tool Handling"""
  
  theme: OutputTheme = Field(
    default=OutputTheme.afterglow, description="Theme for logging"
  )
  
  cache_lifetime_ms: int = Field(
    default=100_000,
    description="How long retrieved tools should be cached in milliseconds."
  )
  
class MCPToolsModule(FlockModule):
  """
  Module that handles the interaction with the Tools of several Model Context Protocol
  Servers. This module will retrieve the necessary tools and modify the agent it is attached to
  to inject the tools into the agent to allow it to call them.
  
  The Module will retrieve the tools the configured 
  MCP Servers provide by hooking into the `initialize`
  lifecycle-hook of the agent(s) it is attached to
  
  NOTE:
    This will ONLY provide access to 'Tools' that the servers provide!
    If you need your agent to interact with Prompts or Resources
    from a server, then see MCPPromptModule, MCPResourceModule.
    
  NOTE:
    It is recommended, that each agent should have its own 
    instance of a MCPToolsModule the avoid confusion
    and enhance readability and making debugging easier.
  
  NOTE:
    It is recommended, that you keep the number of Attached Servers
    within a reasonable range (1 - 4) as MCP Servers may provide
    a lot of tools. Too many tools may confuse the agent 
    or lead to unpredictable outcomes. Start with one (1) Server per
    Module config and test your logic before adding further servers.
  """
  name: str = "mcp.tools"
  config: MCPToolsModuleConfig = Field(
    default_factory=MCPToolsModuleConfig, description="MCP Tool configuration"
  )
  
  def __init__(self, name: str, config: MCPToolsModuleConfig):
    super().__init__(name=name, config=config)
    
  async def initialize(self, agent, inputs, context = None):
    """
    Called when the agent starts running.
    This method checks the availability of the configured MCP-Servers.
    After that, it will fetch the tools from the configured remote servers and cache
    them IF the cache has not already been filled OR the cache contents
    have expired. After retrieval and caching, the retrieved tools
    will be injected into the Agent's list of tools as callables.
    
    NOTE:
      Should a MCP-Tool-Server not be available or produce an error 
      during the availabilty check, a Message will be logged,
      BUT AGENT EXECUTION AND RUNNING WILL ONLY BE HALTED IF THE MCP-TOOL SERVER
      HAS BEEN CONFIGURED WITH `abort_on_error`=`True`!
      Otherwise, the error will be logged, but execution will not be halted.
    """
    return await super().initialize(agent, inputs, context)
  
  async def pre_evaluate(self, agent, inputs, context = None):
    """
    Called before agent evaluation, can modify inputs.
    This will check the cache of tools for the agent.
    If the cache contents have expired, it will re-fetch the tools
    and update the list of tools for the agent.
    """
    return await super().pre_evaluate(agent, inputs, context)
  
  async def post_evaluate(self, agent, inputs, result, context = None):
    """
    Called after agent evaluation, can modify results.
    """
    return await super().post_evaluate(agent, inputs, result, context)
  
  async def terminate(self, agent, inputs, result, context = None):
    """
    Called when the agent finishes running.
    """
    return await super().terminate(agent, inputs, result, context)
  
  async def on_error(self, agent, error, inputs, context = None):
    """
    Called when an error occurs during agent execution.
    """
    return await super().on_error(agent, error, inputs, context)