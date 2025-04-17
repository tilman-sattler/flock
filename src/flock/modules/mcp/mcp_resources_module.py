"""
Module for handling MCP-Provided Resources
"""

from typing import TYPE_CHECKING, Any

from mcp import StdioServerParameters
from pydantic import Field

if TYPE_CHECKING:
  from flock.core import FlockAgent

from flock.core.context.context import FlockContext
from flock.core.flock_module import FlockModule, FlockModuleConfig
from flock.core.logging.formatters.themed_formatter import ThemedAgentResultFormatter
from flock.core.logging.formatters.themes import OutputTheme
from flock.core.logging.logging import get_logger


logger = get_logger("module.mcp_resources")

class MCPResourcesModule(FlockModule):
  """
  Module that handles the interaction with the Resources exposed by one or more configured MCP-Servers.
  For more info on MCP-Resources see: https://modelcontextprotocol.io/docs/concepts/resources
  
  NOTE:
    Resources are a core primitive in the Model Context Protocol (MCP) that
    allow servers to expose data and content that can be read by clients and used
    as context for LLM interactions.
  NOTE:
    Resources represent any kind of data that an MCP server wants to make available to clients.
    This can include:
      - File contents
      - Database records
      - API responses
      - Live system data
      - Screenshots and images
      - Log files
      - And more
    Each Resource is identitfied by a unique URI that can contain either text or binary data
  """