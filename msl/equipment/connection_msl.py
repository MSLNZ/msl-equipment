"""
Use MSL resources to establish a connection to the equipment.
"""
import time

import serial

from msl.loadlib import LoadLibrary
from msl.equipment import constants
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
        lib_path = str(record.connection.address.split('::')[2])
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
    _encoding = 'utf-8'
    _read_size = 2**14

    chunk_size = _read_size

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
        self._read_termination = '' if termination is None else str(termination)

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

    @property
    def chunk_size(self):
        """:obj:`int`: The number of bytes to be :meth:`read`."""
        return self._read_size

    @property
    def read_size(self):
        """:obj:`int`: The number of bytes to be :meth:`read`."""
        return self._read_size

    @read_size.setter
    def read_size(self, size):
        """The number of bytes to be :meth:`read`."""
        size = int(size)
        if size < 1:
            raise ValueError('The number of bytes to read must be >0')
        self._read_size = size

    def read(self, size=None):
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
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    ask = query


class ConnectionSerial(ConnectionMessageBased):

    def __init__(self, record):
        """Establish a connection through a Serial port.

        The :obj:`record.connection.properties <msl.equipment.record_types.ConnectionRecord.properties>`
        dictionary for a Serial connection supports the following key-value pairs::

            'read_termination': str or None
            'write_termination': str or None
            'read_size': int (the number of bytes to be read, must be > 0)
            'encoding': str (e.g., 'ascii')
            'baud_rate': int (e.g., 9600, 115200)
            'data_bits': int (e.g., 5, 6, 7, 8)
            'stop_bits': int or float (e.g., 1, 1.5, 2)
            'parity': str (e.g., none, even, odd, mark, space)
            'timeout': float or None (the read timeout value)
            'write_timeout': float or None (the write timeout value)
            'inter_byte_timeout': float or None (the inter-character timeout)
            'exclusive': bool (set exclusive access mode, for POSIX only)
            'xon_xoff': bool (enable software flow control)
            'rts_cts': bool (enable hardware (RTS/CTS) flow control)
            'dsr_dtr': bool (enable hardware (DSR/DTR) flow control)
        """
        ConnectionMessageBased.__init__(self, record)

        props = record.connection.properties

        self._serial = serial.Serial()

        self.read_termination = props.get('read_termination', self.read_termination)
        self.write_termination = props.get('write_termination', self.write_termination)
        self.read_size = props.get('read_size', self.read_size)
        self.encoding = props.get('encoding', self.encoding)
        self._serial.port = record.connection.address.split('::')[0]
        self._serial.parity = props.get('parity', constants.Parity.NONE).value
        self._serial.timeout = props.get('timeout', None)
        self._serial.write_timeout = props.get('write_timeout', None)
        self._serial.inter_byte_timeout = props.get('inter_byte_timeout', None)
        self._serial.exclusive = props.get('exclusive', None)
        self._serial.xonxoff = props.get('xon_xoff', False)
        self._serial.rtscts = props.get('rts_cts', False)
        self._serial.dsrdtr = props.get('dsr_dtr', False)

        if 'baud_rate' in props:
            self._serial.baudrate = props['baud_rate']
        else:
            self._serial.baudrate = props.get('baudrate', 9600)

        if 'data_bits' in props:
            self._serial.bytesize = props['data_bits']
        else:
            self._serial.bytesize = props.get('bytesize', constants.DataBits.EIGHT).value

        if 'stop_bits' in props:
            self._serial.stopbits = props['stop_bits'].value
        else:
            self._serial.stopbits = props.get('stopbits', constants.StopBits.ONE).value

        try:
            error_msg = ''
            self._serial.open()
        except serial.serialutil.SerialException as e:
            error_msg = str(e)

        if error_msg:
            self.raise_exception(error_msg)

        self.log_debug('Connected to {}'.format(record.connection))

    @property
    def serial(self):
        """:obj:`serial.Serial`: The reference to the Serial object."""
        return self._serial

    @property
    def baud_rate(self):
        """:obj:`int`: The baud rate setting."""
        return self._serial.baudrate

    @property
    def data_bits(self):
        """:obj:`~.constants.DataBits`: The number of data bits."""
        return constants.DataBits(self._serial.bytesize)

    @property
    def stop_bits(self):
        """:obj:`~.constants.StopBits`: The stop bit setting."""
        return constants.StopBits(self._serial.stopbits)

    @property
    def parity(self):
        """:obj:`~.constants.Parity`: The parity setting."""
        return constants.Parity(self._serial.parity)

    def write(self, message):
        """Write the given message over the serial port.

        Parameters
        ----------
        message : :obj:`str`
            The message to write.

        Returns
        -------
        :obj:`int`:
            The number of bytes written to the serial port.
        """
        data = (message + self.write_termination).encode(self.encoding)
        self.log_debug('{}.write({})'.format(self.__class__.__name__, data))
        return self._serial.write(data)

    def read(self, size=None):
        """Read `size` bytes from the serial port.

        If a `timeout` is set it may return less characters as requested. With no
        `timeout` it will block until the requested number of bytes is read.

        Parameters
        ----------
        size : :obj:`int`
            The number of bytes to read. If :obj:`None` then read :obj:`.read_size` bytes.

        Returns
        -------
        :obj:`bytes`:
            The bytes read from the serial port.
        """
        size = self.read_size if size is None else size
        b = self._serial.read(size)
        self.log_debug('{}.read({}) -> {}'.format(self.__class__.__name__, size, b))
        return b

    def disconnect(self):
        self._serial.close()
