from flock.core.exception.flock_exception import FlockException


class FlockMCPConnectionException(FlockException):
  """
  Description:
    Exception raised when a connection to a MCP-Server fails for whatever
    reason.
  Attributes:
    `message` (str): explanation of the error
  """
  
  def __init__(self, message: str, *args):
    super().__init__(message, *args)