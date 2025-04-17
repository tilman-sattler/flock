class FlockConfigurationException(Exception):
  """
  Description:
    Exception raised in the case of faulty configuration in Flock components
  
  Attributes:
    message (str): explanation of the error.
  """
  
  def __init__(self, message):
    self.message = message
    super().__init__(message)