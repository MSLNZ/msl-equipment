"""
Use MSL resources to establish a connection to the equipment.
"""
import logging

from msl.equipment.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionMSL(Connection):

    CR = '\r'
    """:py:class:`str`: The carriage-return character"""

    LF = '\n'
    """:py:class:`str`: The line-feed character"""

    _read_termination = None
    _write_termination = CR + LF
    _encoding = 'ascii'

    def __init__(self, record):
        """
        Use MSL resources to establish a connection to the equipment.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` to use this
        class for the communication system. This is achieved by setting the value in the **Backend** 
        field for a connection record in the **Connections** database to be **MSL**.

        Args:
            record (:class:`~.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.
        """
        Connection.__init__(self, record)

    @property
    def encoding(self):
        """
        :py:class:`str`: The encoding that is used for :meth:`~.Connection.read` 
        and :meth:`~.Connection.write` operations.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """
        Set the encoding to use for :meth:`~.Connection.read` and 
        :meth:`~.Connection.write` operations.
        """
        _ = 'test encoding'.encode(encoding).decode(encoding)
        self._encoding = encoding

    @property
    def read_termination(self):
        """
        :py:class:`str` or :py:data:`None`: The termination character sequence that is 
        used for :meth:`~.Connection.read` operations.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination):
        """
        Set the termination character sequence to use for :meth:`~.Connection.read` 
        operations.

        Args:
            termination (str): Reading stops when the equipment stops sending data 
                (e.g., by setting appropriate bus lines) or the ``read_termination`` 
                character sequence is detected.
        """
        self._read_termination = termination if termination is None else str(termination)

    @property
    def write_termination(self):
        """
        :py:class:`str`: The termination character sequence that is appended to 
        :meth:`~.Connection.write` messages.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        """
        Set the termination character sequence to append to :meth:`~.Connection.write` 
        messages.

        Args:
            termination (str): The character sequence to append to 
                :meth:`~.Connection.write` messages.
        """
        self._write_termination = '' if termination is None else str(termination)
