"""
Simulate a connection to the equipment.
"""
import random
import logging

from msl.equipment.connection import Connection

# create a demo logger level between INFO and WARNING
logging.DEMO = logging.INFO + 5
logging.addLevelName(logging.DEMO, 'DEMO')

logger = logging.getLogger(__name__)


class ConnectionDemo(Connection):

    def __init__(self, record):
        """
        :class:`Logs <demo_logger>` that a connection has been established.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`EquipmentRecord.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An
                equipment record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        Connection.__init__(self, record)
        logger.demo("Connected to {}".format(self.record.connection))
        self._message = None

    def disconnect(self):
        """
        :class:`Logs <demo_logger>` a disconnection from the equipment.
        """
        logger.demo("Disconnected from {}".format(self.record.connection))

    def write(self, message, termination=None, encoding=None):
        """
        :class:`Logs <demo_logger>` the write message.

        Returns:
            :py:class:`int`: -1 (to indicate that no bytes were actually written to the equipment).
        """
        if len(message.strip()) == 0:
            raise RuntimeError('Cannot write an empty message')

        logger.demo("{}.write('{}')".format(self.record.connection, message))
        self._message = message
        return -1

    def read(self, termination=None, encoding=None):
        """
        :class:`Logs <demo_logger>` the simulated response.

        Returns:
            :py:class:`str`: The string ``demo:`` + the simulated response.
        """
        if self._message is None:
            raise RuntimeError('Cannot call read() without first calling write(message)')

        if self._message == '*IDN?':
            value = '{}, {}, {}'.format(self.record.manufacturer, self.record.model, self.record.serial)
        else:
            value = random.random()

        self._message = None
        logger.demo('{}.read() -> {}'.format(self.record.connection, value))
        return 'demo:{}'.format(value)


def demo_logger(self, message, *args, **kws):
    """
    A custom logger for :class:`.ConnectionDemo` objects. The logging
    level is set to be between the :py:data:`logging.INFO` and :py:data:`logging.WARNING`
    `logging levels <https://docs.python.org/3/library/logging.html#logging-levels>`_.
    """
    if self.isEnabledFor(logging.DEMO):
        self._log(logging.DEMO, message, args, **kws)

logging.Logger.demo = demo_logger
