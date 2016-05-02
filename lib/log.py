import os
import logging
import logging.config

def setup_logging():
  
  formatter = logging.Formatter("%(asctime)s - %(levelname)s - (%(name)s) - %(message)s")

  logger = logging.getLogger('newapp')
  logger.setLevel(logging.INFO)

  handler = logging.StreamHandler()
  handler.setLevel(logging.INFO)
  handler.setFormatter(formatter)

  errorhandler = logging.StreamHandler()
  errorhandler.setLevel(logging.ERROR)
  errorhandler.setFormatter(formatter)

  logger.addHandler(errorhandler)
  logger.addHandler(handler)
