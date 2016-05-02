import os

HOME = '/var/log'
HOME = os.environ.get('LOG_HOME') or HOME
LOG_DIR = 'newapp'
LOG_FILE = 'newapp.log'
DEBUG_LOG_FILE = 'newapp_debug.log'
ERROR_LOG_FILE = 'newapp_error.log'

PORT = 9000
