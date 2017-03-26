"""
Simulate a connection to the equipment.
"""
import random
import logging

from msl.equipment.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionDemo(Connection):

    def __init__(self, record):
        """
        :class:`Logs <demo_logger>` that a connection has been established.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        Args:
            record (:class:`~.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.
        """
        Connection.__init__(self, record)
        logger.demo("Connected to {}".format(self.record.connection))
        self._message = None

    def disconnect(self):
        """
        :class:`Logs <demo_logger>` a disconnection from the equipment.
        """
        logger.demo("Disconnected from {}".format(self.record.connection))

    def write(self, message):
        """
        :class:`Logs <demo_logger>` the write message.

        Returns:
            :py:class:`int`: To indicate that no bytes were actually written to 
            the equipment a value of -1 is returned.
        """
        if len(message.strip()) == 0:
            raise RuntimeError('Cannot write an empty message')

        logger.demo("{}.write('{}')".format(self.record.connection, message))
        self._message = message
        return -1

    def read(self):
        """
        :class:`Logs <demo_logger>` the simulated response.

        Returns:
            :py:class:`str`: The string ``demo:`` + the simulated response.
        """
        if self._message is None:
            raise RuntimeError('Cannot call read() without first calling write(message)')

        # TODO add elif statements to return a more appropriate response base on the write message
        if self._message in ('*IDN?', 'V'):
            value = '{}, {}, {}'.format(self.record.manufacturer, self.record.model, self.record.serial)
        else:
            value = random.random()

        self._message = None
        logger.demo('{}.read() -> {}'.format(self.record.connection, value))
        return 'demo:{}'.format(value)


# create a demo logger level between INFO and WARNING
logging.DEMO = logging.INFO + 5
logging.addLevelName(logging.DEMO, 'DEMO')


def demo_logger(self, message, *args, **kws):
    """
    A custom logger for :class:`.ConnectionDemo` objects. The logging
    level is set to be between the :py:data:`logging.INFO` and :py:data:`logging.WARNING`
    `logging levels <log_level_>`_ and you can set the `log level <log_level_>`_ to be 
    a :py:data:`logging.DEMO` value.
    
    .. _log_level: https://docs.python.org/3/library/logging.html#logging-levels
    """
    if self.isEnabledFor(logging.DEMO):
        self._log(logging.DEMO, message, args, **kws)

logging.Logger.demo = demo_logger
