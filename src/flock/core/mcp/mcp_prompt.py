from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from mcp.types import PromptArgument


class MCPPrompt(BaseModel):
  
  name: str = Field(
    description="The name of the Prompt or Prompt template",
  )
  
  description: Optional[str] = Field(
    default=None,
    description="An optional description of what this prompt provides"
  )
  
  arguments: Optional[List[PromptArgument]] = Field(
    default=None,
    description="A list of arguments to use for templating the prompt."
  )
  
  model_config: ConfigDict = Field(
    description=""
  )
  
  role: Literal["user", "assistant", "system"] = Field(
    description="Type of the Prompt"
  )
  
  content_type: Literal["text"] = Field(
    description="Content-Type of the Prompt"
  )
  
  text: str = Field(
    description="The actual prompt itself"
  )