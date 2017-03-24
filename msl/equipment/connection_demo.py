import random
import logging

from msl.equipment.connection import Connection

logger = logging.getLogger(__name__)

# create a demo logger level between INFO and WARNING
logging.DEMO = logging.INFO + 5
logging.addLevelName(logging.DEMO, 'DEMO')

def demo_logger(self, message, *args, **kws):
    if self.isEnabledFor(logging.DEMO):
        self._log(logging.DEMO, message, args, **kws)

logging.Logger.demo = demo_logger


class ConnectionDemo(Connection):

    def __init__(self, equipment_record):
        Connection.__init__(self, equipment_record)
        self._message = ''

    def write(self, message):
        logger.demo('{}.write("{}")'.format(self.record, message))
        self._message = message

    def read(self):
        if self._message == '*IDN?':
            value = '{}, {}, {}'.format(self.record.manufacturer, self.record.model, self.record.serial)
        else:
            value = 'random:{}'.format(random.random())

        logger.demo('{}.read() -> {}'.format(self.record, value))
        return value
