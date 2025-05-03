from pydantic import BaseModel


class MCPTool(BaseModel):
    """
    Description:
      Object representing a MCP-Tool retrieved from an MCP-Server.
      implements __call__.
      __call__ is being implemented because dspy requires callables
    """

    def __call__(self, *args, **kwds):
        return super().__call__(*args, **kwds)
