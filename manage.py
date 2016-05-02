# Always keep the monkeypatching above anything.
# Otherwise any library before it will use unpatched sockets and threads
import gevent.monkey
gevent.monkey.patch_all()

from apps import create_app
import os
import sys
import newrelic.agent
from flask_script import Manager
from flask_script import Server
import config

# "staging" for Staging
# "production" for Production
env = os.environ.get('HOSTENV') or 'development'

if env == "production":
  newrelic_cfg_file = os.path.join(os.getcwd(), "conf", "newapp-newrelic-%s.ini" % env)
  newrelic.agent.initialize(newrelic_cfg_file)

app = create_app()
app.config['DEBUG'] = True
manager = Manager(app)
manager.add_command("runserver", Server(host="127.0.0.1", port=config.PORT))

@manager.command
def test(coverage=False):
  """Run the unit tests."""
  pass

if __name__ == '__main__':
  manager.run()
