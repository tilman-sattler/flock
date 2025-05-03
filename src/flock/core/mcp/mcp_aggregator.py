from pydantic import BaseModel, Field

from flock.core.context.context import FlockContext


class MCPAggregator(BaseModel):
    """
    Description:

    """

    initialized: bool = Field(
        default=False,
        description="Whether or not the aggregator has been initialized."
    )

    persistent_connections: bool = Field(
        default=False,
        description="Whether or not to maintain persistent connections to the servers."
    )

    server_names: list[str] = Field(
        description="A List of Server names to connect to"
    )

    context: FlockContext | None = Field(
        default=None,
        exclude=True,
        description="Global Flock Context"
    )

    async def __aenter__(self) -> "MCPAggregator":
