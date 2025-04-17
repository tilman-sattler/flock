class FlockException(Exception):
  """
  Description:
    Base Exception Class for all Flock Exceptions.
  
  Attributes:
    `message` (str): explanation of the error.
  """
  
  def __init__(self, message: str, *args):
    super().__init__(*args)
    self.message = message