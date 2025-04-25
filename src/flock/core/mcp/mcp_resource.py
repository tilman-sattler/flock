from pydantic import BaseModel, Field
from mcp.types import BlobResourceContents, TextResourceContents, ResourceContents

class MCPResource(BaseModel):
  
  uri: str = Field(
    description="URI of the resource",
  )
  
  contents: ResourceContents = Field(
    description="The resource Contents"
  )