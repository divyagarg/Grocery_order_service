import os
import logging
import logging.config
from config import LOG_DIR, LOG_FILE, ERROR_LOG_FILE, APP_NAME


def setup_logging(config):
    if not os.path.exists(config.HOME):
        os.makedirs(config.HOME)

    log_dir = os.path.join(config.HOME, LOG_DIR)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        "[ %(asctime)s - %(levelname)s - %(pathname)s - %(module)s - %(funcName)s - %(lineno)d ] - %(message)s")

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)

    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_dir, LOG_FILE), 'midnight')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    errorhandler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_dir, ERROR_LOG_FILE), 'midnight')
    errorhandler.setLevel(logging.ERROR)
    errorhandler.setFormatter(formatter)

    logger.addHandler(errorhandler)
    logger.addHandler(handler)
