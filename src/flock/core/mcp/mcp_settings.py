from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from uuid import uuid4


class MCPAuthenticationSettings(BaseModel):
    """
    Description:
      Represents authentication settings for an MCP-Server.
    """

    api_key: str | None = Field(
        default=None,
        description="API-Key for the server."
    )

    model_config: ConfigDict = Field(
        default=ConfigDict(extra="allow", arbitrary_types_allowed=True),
        description="Config dict."
    )


class MCPRootSetting(BaseModel):
    """
    Description:
        Describes the roots an MCP server may provide.
        More info: https://modelcontextprotocol.io/docs/concepts/roots
    """

    uri: str = Field(
        description="The URI identifying the currently used root. Must start with `file://` or `http://` or `https://`"
    )

    root_name: Optional[str] = Field(
        default=None,
        description="(optional) The name for the root."
    )

    uri_alias: str | None = Field(
        default=None,
        description="(optional) Alias for the root when talking to the server. For example, you have a gitlab repo that you are working on which is private and a github-mirror which is public. The server may want the uri for the public github-mirror as it can't access the private gitlab repo."
    )

    @field_validator("uri", "uri_alias")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """
        Validate that `self.uri` and `self.uri_alias` start with either `file://`, `http://`, or `https://`
        """
        if v:
            if not v.startswith("file://") or v.startswith("http://") or v.startswith("https://"):
                raise ValueError(
                    f"Root URI not valid. Got: {v}. uri / uri_alias must start with either `file://`, `http://` or `https://`")
        return v

    model_config: ConfigDict = Field(
        default=ConfigDict(extra="allow", arbitrary_types_allowed=True),
        description="Model Config."
    )


class MCPSamplingSettins(BaseModel):
    """
    Description:
        Settings for Samplin.
        In the context of MCP, Sampling is a feature which 
        allows a server to request using the LLM of the client
        to generate a completion.
        How it works:
            1. The server sends a `sampling/CreateMessage` request to the client (an agent for example)
            2. The client reviews the request and can modify it.
            3. The client uses it's LLM to generate a text based on the request.
            4. The client reviews the completion
            5. The client returns the result to the server.
    """
    model: str = Field(
        default="azure/gpt-4o",
        description="The model to use for sampling."
    )

    model_config: ConfigDict = Field(
        default=ConfigDict(extra="allow", arbitrary_types_allowed=True),
        description="Model Config."
    )


class MCPConnectionSettings(BaseModel):
    """
    Description:
      Represents the configuration for a connection to 
      A MCP-Server. (local or remote)
    """

    name: str = Field(
        default="mcp_server_" + uuid4(),
        description="The name of the server. If not explicitly set, a random name will be generated."
    )

    description: str | None = Field(
        default=None,
        description="A description for the server"
    )

    transport_type: Literal["stdio", "sse", "websockets"] = Field(
        description="The underlying transport mechanism that should be used."
    )

    command: str | None = Field(
        default=None,
        description="If the server is a locally running one, then this needs to contain the command to start the server."
    )

    args: List[str] | None = Field(
        default=None,
        description="Additional arguments to be passed to a locally running server."
    )

    read_timeout_millis: int | None = Field(
        default=None,
        description="The timeout for the session. If no data is being received within this timeframe, the connection will close."
    )

    read_transport_sse_timeout_millis: int | None = Field(
        default=None,
        description="The timeout for waiting for server-sent-events. Connection will close if no events are received within the alloted timeframe."
    )

    url: str | None = Field(
        default=None,
        description="The URL for a remote server."
    )

    additional_headers: Dict[str, str] | None = Field(
        default=None,
        description="Additional Headers to send to a remote server."
    )

    authentication_settings: MCPAuthenticationSettings | None = Field(
        default=None,
        description="Authentication configuration for the server."
    )

    roots: Optional[List[MCPRootSetting]] = Field(
        default=None,
        description="Root directories that the current Agent/Module/Application can access."
    )

    environment: Dict[str, str] | None = Field(
        default=None,
        description="Environment variables to pass to a locally running server process."
    )

    sampling_settings: MCPSamplingSettins | None = Field(
        default=None,
        description="Sampling Settings"
    )


class MCPClientSettings(BaseModel):
    """
    Description:
        Settings to use for configuring an MCPClient.
    """

    connections: Dict[str, MCPConnectionSettings] = Field(
        description="Maps server-names to their connection-settings."
    )

    model_config: ConfigDict = Field(
        default=ConfigDict(extra="allow", arbitrary_types_allowed=True),
        description="Model Config."
    )
