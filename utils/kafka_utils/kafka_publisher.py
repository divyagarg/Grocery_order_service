from config import PUBLISH_TO_KAFKA, APP_NAME
from flask import g
from kafka import SimpleClient, KeyedProducer
import logging
import datetime
from utils.jsonutils.output_formatter import create_data_response

logger = logging.getLogger(APP_NAME)

class Publisher:
    kafka = None
    producer = None
    topic = None


    def __init__(self):
        pass

    @staticmethod
    def init(app):
        Publisher.topic = app.config['KAFKA_TOPIC']
        Publisher.kafka = SimpleClient(app.config['KAFKA_HOSTS'])
        Publisher.producer = KeyedProducer(Publisher.kafka, async=True, batch_send_every_t=0.010)

    @staticmethod
    def publish_message(key, message, **kwargs):
        UUID = g.UUID
        try:
            logger.info('{%s} Publishing data {%s} '%(UUID, message))
            startTime = datetime.datetime.now()

            if PUBLISH_TO_KAFKA:
                Publisher.producer.send_messages(Publisher.topic, str(key), message)

            endTime = datetime.datetime.now()
            total_time = endTime-startTime
            total_time = total_time.seconds*1000000 + total_time.microseconds
            logger.info('{%s} Kafka took {%s} microseconds for publishing'%(UUID, total_time))
            return True
        except Exception as e:
            logger.error('{%s} Exception while publishing', exc_info=True)
            raise Exception(str(e))

    @staticmethod
    def test():
        Publisher.publish_message("test", "This is a test msg")
        return create_data_response()