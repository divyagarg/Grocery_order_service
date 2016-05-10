__author__ = 'divyagarg'

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from enum import Enum

db = SQLAlchemy()


def initialize_db(app):
    db.init_app(app)
    import models
    migrate = Migrate(app, db)


class DELIVERY_TYPE(Enum):
    NORMAL_DELIVERY = 'NORMAL'
    SLOT_DELIVERY = 'SLOTTED'


class ORDER_STATUS(Enum):
    PENDING_STATUS = 'PENDING'
    APPROVED_STATUS = 'APPROVED'
    CREATED = 'CREATED'



class ORDER_SOURCE_REFERENCE(Enum):
    APP = 0
    WEB = 1

class VALID_ORDER_TYPES(Enum):
    PHARMA ='PHARMA'
    GROCERY ='GROCERY'
    NATIONAL = 'NATIONAL'
    NDD = 'NDD'