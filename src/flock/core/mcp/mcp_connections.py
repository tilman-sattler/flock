from pathlib import Path
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field
from pydantic_core import Url

class FlockConnectionConfig(BaseModel):
  """
  
  """
  transport: Literal["stdio", "sse", "websocket", None] = Field(
    default=None,
    description="What type of transport to use under the hood."
  )
  
  additional_session_kwargs: dict[str, Any] | None = Field(
    default=None,
    description="Additional keyword arguments to pass to the ClientSession object."
  )

class FlockStdioConnectionConfig(FlockConnectionConfig):
  """
  
  """
  kind: Literal["script", "binary"] | None = Field(
    default=None,
    description="Whether the server is a script or an executable binary."
  )
  
  interpreter: str | None = Field(
    default=None,
    description="Which interpreter to use if the server is a script."
  )
  
  args: list[str] | None = Field(
    default=None,
    description="Additional arguments when starting the server."
  )
  
  cwd: str | Path | None = Field(
    default=None,
    description="The working directory to use when spawning the server."
  )
  
  text_encoding: Literal["ascii", "utf-8", "utf-16", "utf-32"] | None = Field(
    default="utf-8",
    description="The Char-Encoding to use when communicating with the server. Currently supported: ascii, utf-8, utf-16, utf-32." # TODO: add more encoding formats
  )
  
  handle_text_encoding_error_strategy: Literal["strict", "ignore", "replace"] = Field(
    default="strict",
    description="How to handle encoding errors. https://docs.python.org/3/library/codecs.html#codec-base-classes: 'Errors may be given to set the desired error handling scheme'."
  )
  
class FlockRemoteMCPServerConnectionConfig(FlockConnectionConfig):
  
  base_url: str | Url = Field(
    description="The Base-URL to connect to."
  )
  
class FlockWebsocketConnectionConfig(FlockRemoteMCPServerConnectionConfig):
  """
  
  """

class FlockSSEConnectionConfig(FlockRemoteMCPServerConnectionConfig):
  """
  
  """
  timeout_in_ms: int = Field(
    default=3_000,
    description="The maximum HTTP-Timeout in ms. Defaults to: `3000ms`."
  )
  
  max_retries: int = Field(
    default=3,
    description="The maximum number of Retry-Attempts to connect to the server. Defaults to: `3`."
  )
  
  read_timeout_in_ms: int = Field(
    default=3_000,
    description="SSE read-timeout in ms. Defaults to `3000ms`."
  )
  
  