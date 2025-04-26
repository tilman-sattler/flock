import traceback
from flock.core.mcp.mcp_session import MCPServerConnection


async def _manage_server_session(session: MCPServerConnection) -> None:
    """
    Description:
      Lifecycle management for a connection to a server.
    """

    server_name = session.server_name
    try:
        transport_context = session._transport_context_factory()

        async with transport_context as (read_stream, write_stream):

            session.create_session(
                read_stream=read_stream, write_stream=write_stream)

            async with session.client_session:
                await session.initialize_session()

                await session.wait_for_shutdown_request()
    except Exception as ex:
        # TODO: logging.
        session._error_occurred = True
        session._error_message = traceback.format_exception(ex)
        session._initialize_event.set()
