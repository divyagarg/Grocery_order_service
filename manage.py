# Always keep the monkeypatching above anything.
# Otherwise any library before it will use unpatched sockets and threads
import gevent.monkey

gevent.monkey.patch_all()

from apps import create_app
import os
import newrelic.agent
from flask_script import Manager
from flask_script import Server
from flask_migrate import MigrateCommand
import config

# "staging" for Staging
# "production" for Production
hostenv = os.environ.get('HOSTENV') or 'default'


if hostenv in ["production", "staging"]:
    newrelic_cfg_file = os.path.join(os.getcwd(), "conf", "grocery_order_service-newrelic-%s.ini" % hostenv)
    newrelic.agent.initialize(newrelic_cfg_file)

app = create_app(hostenv)
app.config['DEBUG'] = True
manager = Manager(app)
manager.add_command("runserver", Server(host="127.0.0.1", port=config.PORT))
manager.add_command("db", MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()
