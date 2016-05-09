import time
import functools
import logging
import ujson as json
from flask import Response
logger = logging.getLogger()

def logtime(f):
  @functools.wraps(f)
  def wrapped(*args, **kwargs):
    start = time.time()
    rv = f(*args, **kwargs)
    logger.info('Time taken (for args %s) = %s', args, time.time() - start)
    return rv
  return wrapped

def jsonify(f):
  @functools.wraps(f)
  def wrapped(*args, **kwargs):
    start = time.time()
    try:
      rv = f(*args, **kwargs)
      status_code = 200
      if isinstance(rv, dict) and rv.has_key('status'):
        if rv['status'] != 'success' and rv.has_key('error'):
          if isinstance(rv['error'], dict) and rv['error'].has_key('code'):
            status_code = rv['error']['code']
      resp = Response(
          response=json.dumps(rv), status=status_code,
          mimetype="application/json")
    except Exception as e:
      logger.exception('Error while processing request')
      resp = Response(response=json.dumps({'message': str(e)}), status=500,
        mimetype="application/json")
    logger.info('Total time taken = %s', time.time() - start)
    return resp
  return wrapped

def logrequest(f):
  @functools.wraps(f)
  def wrapped(*args, **kwargs):
    rv = f(*args, **kwargs)
    logger.info("Arguments = %s Returned %s" % (kwargs, rv))
    return rv
  return wrapped