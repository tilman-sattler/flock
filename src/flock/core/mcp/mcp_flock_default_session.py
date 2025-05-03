from typing import TYPE_CHECKING, Optional

from mcp import ClientSession
from mcp.shared.session import (
    ReceiveNotificationT,
    ReceiveResultT,
    RequestId,
    SendNotificationT,
    SendRequestT,
    SendResultT
)
from mcp.types import (
    ErrorData,
    ListRootsResult,
    Root,
)
from pydantic import AnyUrl

from flock.core.mcp.mcp_settings import MCPServerConnection


async def default_list_roots_callback(ctx: ClientSession) -> ListRootsResult:
    """
    Description:
      Default Callback called by the MCP Library on `list_roots`
    Args:
      `ctx` (mcp.ClientSession): The current ClientSession

    Returns:
      ListRootsResult: ListRootsResult
    """
    roots = []
    if (
        hasattr(ctx, "server_config")
        and hasattr(ctx.session, "server_config")
        and ctx.session.server_config
        and hasattr(ctx.session.server_config, "roots")
        and ctx.session.server_config.roots
    ):
        roots = [
            Root(
                uri=AnyUrl(
                    root.uri_alias or root.uri,
                ),
                name=root.name
            )
            for root in ctx.session.server_config.roots
        ]

    return ListRootsResult(roots=roots or [])


class MCPFlockDefaultSession(ClientSession):
    """
    Description:
      The default ClientSession for Flock Agents.

    """

    def __init__(self, *args, **kwargs) -> None:
      # TODO: Sampling support
        super().__init__(*args, **kwargs, list_roots_callback=default_list_roots_callback)
        self.server_config: Optional[MCPServerConnection] = None

    async def send_request(
        self,
        request: SendRequestT,
        result_type: type[ReceiveResultT],
    ) -> ReceiveResultT:
      # TODO: logging
        try:
            result = await super().send_request(request=request, result_type=result_type)
            # TODO: logging
            return result
        except Exception as ex:
            # TODO: logging
            raise

    async def send_notification(self, notification):
        # TODO: logging
        try:
            return await super().send_notification(notification)
        except Exception as ex:
            # TODO: logging
            raise

    async def _send_response(self, request_id, response):
      # TODO: logging
        try:
            return await super()._send_response(request_id, response)
        except Exception as ex:
            # TODO: logging
            raise

    async def _received_notification(self, notification):
      # TODO: logging

        try:
            return await super()._received_notification(notification)
        except Exception as ex:
            raise

    async def send_progress_notification(self, progress_token, progress, total=None):
      # TODO: logging
        try:
            return await super().send_progress_notification(progress_token, progress, total)
        except Exception as ex:
            # TODO: logging
            raise
