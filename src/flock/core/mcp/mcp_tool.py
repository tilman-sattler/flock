from typing import Any, Callable, Optional
from mcp import ClientSession, Tool
from mcp.types import CallToolResult
from pydantic import BaseModel, ConfigDict, Field


class MCPTool(BaseModel):
  
  session: ClientSession = Field(
    exclude=True,
    description="The client session in whose context the call will be executed."
  )
  
  name: str = Field(
    description="name of the tool",
  )
  
  description: Optional[str] = Field(
    default=None,
    description="Description of the tool",
  )
  
  input_schema: dict[str, Any] = Field(
    description="Schema for the input",
  )
  
  model_config: ConfigDict = Field(
    description="A Json Schema object describing the expected parameters for the object."
  )
  
  async def _call_tool(
    self,
    **arguments: dict[str, Any],
  ) -> CallToolResult:
    call_result = await self.session.call_tool(self.name, arguments=arguments)
    return call_result
  
  async def __call__(self, *args, **kwds):
    merged_args = {f"arg{i}": arg for i, arg in enumerate(args)}
    merged_args.update(kwds)
    return await self._call_tool(**merged_args)