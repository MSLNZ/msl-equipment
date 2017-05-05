"""
Use MSL resources to establish a connection to the equipment.
"""
import time

from msl.loadlib import LoadLibrary
from msl.equipment.connection import Connection


class ConnectionSDK(Connection):

    def __init__(self, record, libtype):
        """Base class for equipment that use the SDK provided by the manufacturer
        for the connection.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` 
        to use this class for the communication system. This is achieved by setting the 
        value in the **Backend** field for a connection record in the **Connections** 
        database to be **MSL**.

        Do not instantiate this class directly. Use the factory method, 
        :obj:`msl.equipment.factory.connect`, or the `record` object itself, 
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>`,
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~.database.Database`.

        libtype : :obj:`str` or :obj:`None`
            The library type to use for the calling convention.

            The following values are allowed:

                * **'cdll'** -- for a **__cdecl** library
                * **'windll'** or **'oledll'** -- for a **__stdcall** library (Windows only)
                * **'net'** -- for a **.NET** library

        Raises
        ------
        IOError
            If the Python wrapper class around the SDK cannot be found or if the 
            shared library cannot be found.   
        """
        Connection.__init__(self, record)
        lib_path = record.connection.address.split('::')[2]
        self._lib = LoadLibrary(lib_path, libtype)
        self.log_debug('Connected to {}'.format(self.equipment_record.connection))

    @property
    def sdk_path(self):
        """:obj:`str`: The path to the shared library file."""
        return self._lib.path

    @property
    def sdk(self):
        """The reference to the sdk_ library.
        
        .. _sdk: http://msl-loadlib.readthedocs.io/en/latest/_api/msl.loadlib.load_library.html#msl.loadlib.load_library.LoadLibrary.lib
        """
        return self._lib.lib

    def log_errcheck(self, result, func, arguments):
        """Convenience method for logging an errcheck_ when calling an SDK function.

        .. _errcheck: https://docs.python.org/2/library/ctypes.html#ctypes._FuncPtr.errcheck
        """
        self.log_debug('{}.{}{} -> {}'.format(self.__class__.__name__, func.__name__, arguments, result))
        return result


class ConnectionMessageBased(Connection):

    CR = '\r'
    """:obj:`str`: The carriage-return character"""

    LF = '\n'
    """:obj:`str`: The line-feed character"""

    _read_termination = None
    _write_termination = CR + LF
    _encoding = 'ascii'

    def __init__(self, record):
        """Base class for equipment that use message based communication.        

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` 
        to use this class for the communication system. This is achieved by setting the 
        value in the **Backend** field for a connection record in the **Connections** 
        database to be **MSL**.

        Do not instantiate this class directly. Use the factory method, 
        :obj:`msl.equipment.factory.connect`, or the `record` object itself, 
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>`,
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~.database.Database`.
        """
        Connection.__init__(self, record)

    @property
    def encoding(self):
        """
        :obj:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """Set the encoding to use for :meth:`read` and :meth:`write` operations."""
        _ = 'test encoding'.encode(encoding).decode(encoding)
        self._encoding = encoding

    @property
    def read_termination(self):
        """:obj:`str` or :obj:`None`: The termination character sequence 
        that is used for :meth:`read` operations.
        
        Reading stops when the equipment stops sending data (e.g., by setting appropriate 
        bus lines) or the `read_termination` character sequence is detected.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination):
        """The termination character sequence to use for :meth:`read` operations."""
        self._read_termination = termination if termination is None else str(termination)

    @property
    def write_termination(self):
        """:obj:`str`: The termination character sequence that is appended to
        :meth:`write` messages.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        """The termination character sequence to append to :meth:`write` messages."""
        self._write_termination = '' if termination is None else str(termination)

    def read(self):
        """Read a response from the equipment.

        Returns
        -------
        :obj:`str`
            The response from the equipment.
        """
        raise NotImplementedError

    def write(self, message):
        """Write (send) a message to the equipment.

        Parameters
        ----------
        message : :obj:`str`
            The message to write (send) to the equipment.

        Returns
        -------
        :obj:`int`
            The number of bytes written.
        """
        raise NotImplementedError

    send = write

    def query(self, message, delay=0.0):
        """Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Parameters
        ----------
        message : :obj:`str`
            The message to write (send) to the equipment.
        delay : :obj:`float`
            The time delay, in seconds, to wait between :meth:`write` and 
            :meth:`read` operations.

        Returns
        -------
        :obj:`str`
            The response from the equipment.
        """
        self.log_debug('query: ' + message)
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    ask = query
