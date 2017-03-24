import time
import logging

logger = logging.getLogger(__name__)


class Connection(object):

    _backend = None

    def __init__(self, equipment_record):
        self._equipment_record = equipment_record

    def read(self, termination=None, encoding=None):
        raise NotImplementedError

    def write(self, message, termination=None, encoding=None):
        raise NotImplementedError

    def query(self, message, delay=0.0):
        logger.debug('query: ' + message)
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    ask = query

    def disconnect(self):
        pass

    @property
    def record(self):
        return self._equipment_record

    @property
    def backend(self):
        return self._backend

    def __repr__(self):
        address = 'None' if self.record.connection is None else self.record.connection.address
        return '{}<{}|{}|{} at {}>'.format(self.__class__.__name__,
                                           self.record.manufacturer,
                                           self.record.model,
                                           self.record.serial,
                                           address)

    def __del__(self):
        self.disconnect()
