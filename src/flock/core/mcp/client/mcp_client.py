import asyncio


from typing import Optional
from contextlib import AsyncExitStack


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from pydantic import Field

from flock.core.serialization.serializable import Serializable
from flock.core.logging.logging import get_logger

logger = get_logger("mcp.client")

class MCPClientConfiguration(Serializable):
  """Shared Configuration Type for an MCP Client"""
  name: str = Field(
    default="mcp_client",
    description="Name of the Client for Identification"
  )

  max_retries: int = Field(
    default=3,
    description="How many retries should be undertaken to connect to a MCP-Server"
  )
  

class MCPClient(Serializable):
  
  configuration: MCPClientConfiguration | None = Field(
    default=None,
    description="Configuration for the Client"
  )
  
  
  
  def __init__(self, mcpClientConfiguration: MCPClientConfiguration):
    """Initialize session and client objects"""
    self.configuration = mcpClientConfiguration