__author__ = 'divyagarg'


from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
def initialize_db(app):
    db.init_app(app)
    import models
    migrate = Migrate(app, db)