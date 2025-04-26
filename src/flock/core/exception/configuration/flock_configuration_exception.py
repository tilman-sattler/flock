from flock.core.exception.flock_exception import FlockException


class FlockConfigurationException(FlockException):
  """
  Description:
    Exception raised in the case of faulty configuration in Flock components
  
  Attributes:
    `message` (str): explanation of the error.
  """
  
  def __init__(self, message: str, *args):
    super().__init__(message, *args)