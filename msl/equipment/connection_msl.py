"""
Use MSL resources to establish a connection to the equipment.
"""
import time
import logging

from msl.loadlib import LoadLibrary
from msl.equipment.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionSDK(Connection):

    def __init__(self, record, libtype='cdll'):
        """
        Base class for equipment that use the SDK provided by the manufacturer for
        the connection.

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

            libtype (str, optional): The library type to use for the calling convention.

                The following values are allowed:

                * ``libtype`` = **'cdll'**, for a **__cdecl** library
                * ``libtype`` = **'windll'** or **'oledll'**, for a **__stdcall** library (Windows only)
                * ``libtype`` = **'net'**, for a **.NET** library

                Default is **'cdll'**.

        Raises:
            IOError: If the Python wrapper class cannot be found or if the shared library cannot be found.   
        """
        Connection.__init__(self, record)

        libpath = record.connection.address.split('::')[2]
        self._lib = LoadLibrary(libpath, libtype)

    @property
    def sdk_path(self):
        """:py:class:`str`: The path to the shared library"""
        return self._lib.path

    @property
    def sdk(self):
        """The reference to the ctypes/.NET object."""
        return self._lib.lib


class ConnectionMessageBased(Connection):

    CR = '\r'
    """:py:class:`str`: The carriage-return character"""

    LF = '\n'
    """:py:class:`str`: The line-feed character"""

    _read_termination = None
    _write_termination = CR + LF
    _encoding = 'ascii'

    def __init__(self, record):
        """
        Base class for equipment that use message based communication.

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
        :py:class:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """
        Set the encoding to use for :meth:`read` and :meth:`write` operations.
        """
        _ = 'test encoding'.encode(encoding).decode(encoding)
        self._encoding = encoding

    @property
    def read_termination(self):
        """
        :py:class:`str` or :py:data:`None`: The termination character sequence that is 
        used for :meth:`read` operations.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination):
        """
        Set the termination character sequence to use for :meth:`read` 
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
        :meth:`write` messages.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        """
        Set the termination character sequence to append to :meth:`write` messages.

        Args:
            termination (str): The character sequence to append to :meth:`write` messages.
        """
        self._write_termination = '' if termination is None else str(termination)

    def read(self):
        """
        Read a response from the equipment.

        Returns:
            :py:class:`str`: The response from the equipment.
        """
        raise NotImplementedError

    def write(self, message):
        """
        Write (send) a message to the equipment.

        Args:
            message (str): The message to write (send) to the equipment.

        Returns:
            :py:class:`int`: The number of bytes written.
        """
        raise NotImplementedError

    send = write

    def query(self, message, delay=0.0):
        """
        Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Args:
            message (str): The message to write (send) to the equipment.
            delay (float): The time delay, in seconds, to wait between :meth:`write` 
                and :meth:`read` operations.

        Returns:
            :py:class:`str`: The response from the equipment.
        """
        logger.debug('query: ' + message)
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    ask = query
