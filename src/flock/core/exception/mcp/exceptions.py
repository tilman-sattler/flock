from flock.core.exception.flock_exception import FlockException


class FlockMCPClientException(FlockException):
    """
    Description:
      Used to indicate an exception in the 
      execution context of a Flock-MCP Client.

    Attributes:
      `message` (str): explanation of the exception.
      `server_name` (str): The name of the server involved in the exception.
    """

    def __init__(self, message: str, server_name: str, *args):
        super().__init__(message=message, *args)
        self.server_name = server_name


class FlockMCPServerInitializationException(FlockException):
    """
    Description:
      Exception raised when a connection to a MCP-Server fails for whatever
      reason.
    Attributes:
      `message` (str): explanation of the exception
      `server_name` (str): name of the server involved in the exception
    """

    def __init__(self, message: str, server_name: str, *args):
        super().__init__(message, *args)
        self.server_name = server_name
