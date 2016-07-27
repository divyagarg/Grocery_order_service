import os
import logging
import logging.config
from config import LOG_DIR, LOG_FILE, ERROR_LOG_FILE, APP_NAME, DB_FILE


def setup_logging(config):
    if not os.path.exists(config.HOME):
        os.makedirs(config.HOME)

    log_dir = os.path.join(config.HOME, LOG_DIR)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        "[ %(asctime)s %(levelname)s %(pathname)s %(module)s %(funcName)s %(lineno)d ] %(message)s")

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)

    handler = logging.handlers.WatchedFileHandler(os.path.join(log_dir, LOG_FILE), mode='a', encoding='UTF-8', delay=True)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    errorhandler = logging.handlers.WatchedFileHandler(os.path.join(log_dir, ERROR_LOG_FILE), mode='a', encoding='UTF-8', delay=True)
    errorhandler.setLevel(logging.ERROR)
    errorhandler.setFormatter(formatter)

    logger.addHandler(errorhandler)
    logger.addHandler(handler)

    orm_logger = logging.getLogger('sqlalchemy.engine')
    orm_logger.setLevel(logging.INFO)

    orm_handler = logging.handlers.WatchedFileHandler(os.path.join(log_dir, DB_FILE), mode='a', encoding='UTF-8', delay=True)
    orm_handler.setLevel(logging.INFO)
    orm_handler.setFormatter(formatter)

    orm_logger.addHandler(orm_handler)