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
    CANCELLED = 'CANCELLED'


class ORDER_SOURCE_REFERENCE(Enum):
    APP = 0
    WEB = 1


class VALID_ORDER_TYPES(Enum):
    grocery = 0
    bazzar = 1
    pharma = 2

order_types= {}
order_types[0] = 'grocery'
order_types[1] ='bazzar'
order_types[2] = 'pharma'




class PAYMENT_MODE(Enum):
    COD = 0
    PREPAID =1

payment_modes_dict = {}
payment_modes_dict[0] = 'COD'
payment_modes_dict[1] = 'PREPAID'