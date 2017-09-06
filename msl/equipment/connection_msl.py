"""
Use :ref:`resources` to establish a connection to the equipment.
"""
import re
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
        value in the **Backend** field for a connection record in the :ref:`connection_database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.

        libtype : :obj:`str`
            The library type to use for the calling convention.
            See :class:`~msl.loadlib.load_library.LoadLibrary` for more information.

        Raises
        ------
        IOError
            If the shared library cannot be loaded.
        TypeError
            If either `record` or `libtype` is invalid.
        """
        Connection.__init__(self, record)
        lib_path = str(record.connection.address.split('::')[-1])  # the last item must be the path
        self._lib = LoadLibrary(lib_path, libtype)
        self.log_debug('Connected to {}'.format(self.equipment_record.connection))

    @property
    def sdk_path(self):
        """:obj:`str`: The path to the shared library file."""
        return self._lib.path

    @property
    def sdk(self):
        """The reference to the shared library, see :obj:`~msl.loadlib.load_library.LoadLibrary.lib`."""
        return self._lib.lib

    def log_errcheck(self, result, func, arguments):
        """Convenience method for logging an errcheck_ when calling an SDK function.

        .. _errcheck: https://docs.python.org/2/library/ctypes.html#ctypes._FuncPtr.errcheck
        """
        self.log_debug('{}.{}{} -> {}'.format(self.__class__.__name__, func.__name__, arguments, result))
        return result


class ConnectionMessageBased(Connection):

    CR = '\r'
    """:obj:`str`: The carriage-return character."""

    LF = '\n'
    """:obj:`str`: The line-feed character."""

    def __init__(self, record):
        """Base class for equipment that use message-based communication.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` 
        to use this class for the communication system. This is achieved by setting the 
        value in the **Backend** field for a connection record in the :ref:`connection_database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        Connection.__init__(self, record)

        self._read_termination = ConnectionMessageBased.LF
        self._write_termination = ConnectionMessageBased.CR + ConnectionMessageBased.LF
        self._encoding = 'utf-8'
        self._read_size = 2**16
        self._timeout = None

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
        self._read_termination = None if termination is None else str(termination)

    @property
    def write_termination(self):
        """:obj:`str`: The termination character sequence that is appended to
        :meth:`write` messages.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        """The termination character sequence to append to :meth:`write` messages."""
        self._write_termination = None if termination is None else str(termination)

    @property
    def read_size(self):
        """:obj:`int`: The maximum number of bytes to be :meth:`read`."""
        return self._read_size

    @read_size.setter
    def read_size(self, size):
        """The number of bytes to be :meth:`read`."""
        if not isinstance(size, int) or size < 1:
            raise ValueError('The number of bytes to read must be >0 and an integer, got {}'.format(size))
        self._read_size = int(size)

    @property
    def timeout(self):
        """:obj:`int`, :obj:`float` or :obj:`None`: The timeout, in seconds, for I/O operations."""
        return self._timeout

    @timeout.setter
    def timeout(self, seconds):
        """Set the timeout, in seconds, for I/O operations."""
        if seconds is not None:
            if not isinstance(seconds, (int, float)) or seconds < 0:
                raise ValueError('Not a valid timeout value: {}'.format(seconds))
        self._timeout = seconds

    def read(self, size=None):
        """Read the response from the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        size : :obj:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :obj:`str`
            The response from the equipment.
        """
        raise NotImplementedError

    def write(self, message):
        """Write a message to the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        message : :obj:`str`
            The message to write to the equipment.

        Returns
        -------
        :obj:`int`
            The number of bytes written.
        """
        raise NotImplementedError

    def query(self, message, delay=0.0):
        """Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Parameters
        ----------
        message : :obj:`str`
            The message to write to the equipment.
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


class ConnectionSerial(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a Serial port.

        The :obj:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a Serial connection supports the following key-value pairs in the
        :ref:`connection_database`::

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

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connection_database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.

        Raises
        ------
        :exc:`~.exceptions.MSLConnectionError`
            If the Serial port cannot be opened.
        """
        ConnectionMessageBased.__init__(self, record)

        props = record.connection.properties

        self._serial = serial.Serial()

        self.read_termination = props.get('read_termination', self.read_termination)
        self.write_termination = props.get('write_termination', self.write_termination)
        self.read_size = props.get('read_size', self.read_size)
        self.encoding = props.get('encoding', self.encoding)
        self.timeout = props.get('timeout', None)

        # PyVISA and PyVISA-py accept various resource names: 'ASRL', 'COM', 'LPT', 'ASRLCOM'
        # but Serial seems to only be happy with 'COM'
        number = re.search('\d+', record.connection.address)  # get the port number from the address
        if number is None:
            self.raise_exception('No port number was specified -- address={}'.format(record.connection.address))
        self._serial.port = 'COM{}'.format(number.group(0))

        self._serial.parity = props.get('parity', constants.Parity.NONE).value
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

    @ConnectionMessageBased.timeout.setter
    def timeout(self, seconds):
        self._serial.timeout = seconds
        self._timeout = self._serial.timeout

    def disconnect(self):
        """Close the Serial port."""
        try:
            # if the subclass raised an error in the constructor before
            # the this class is initialized then self._serial won't exist
            self._serial.close()
        except AttributeError:
            pass

    def write(self, message):
        """Write the given message over the Serial port.

        Parameters
        ----------
        message : :obj:`str`
            The message to write.

        Returns
        -------
        :obj:`int`:
            The number of bytes written to the Serial port.
        """
        if self.write_termination is not None and not message.endswith(self.write_termination):
            message += self.write_termination
        data = message.encode(self.encoding)
        self.log_debug('{}.write({})'.format(self.__class__.__name__, data))
        return self._serial.write(data)

    def read(self, size=None):
        """Read `size` bytes from the Serial port.

        Parameters
        ----------
        size : :obj:`int`
            The number of bytes to read. If a :obj:`timeout` value is set then it may return
            less bytes than requested. With no :obj:`timeout` it will block until the requested
            number of bytes is read.

            If `size` is :obj:`None` then either read until:

            1. the :obj:`.read_termination` bytes are read (only if the termination value is not :obj:`None`)
            2. :obj:`.read_size` bytes have been read
            3. a :obj:`timeout` occurs (if a :obj:`timeout` has been set)

            This method will block until at least one of the above is fulfilled.

        Returns
        -------
        :obj:`str`:
            The response from the equipment.
        """
        size = self.read_size if size is None else int(size)
        term_char = None if self.read_termination is None else self.read_termination.encode(self.encoding)
        out = bytes()
        start = time.time()
        while True:
            b = self._serial.read(1)
            out += b
            if term_char is not None and out.endswith(term_char):
                out = out[:-len(term_char)]
                break
            if len(out) == size:
                msg = '{}.read() READ MAXIMUM NUMBER OF BYTES [{}], {} BYTES CURRENTLY IN BUFFER'
                self.log_warning(msg.format(self.__class__.__name__, len(out), self._serial.in_waiting))
                break
            if self.timeout is not None and time.time() - start >= self.timeout:
                msg = '{}.read() TIMEOUT OCCURRED'.format(self.__class__.__name__)
                self.log_warning(msg)
                if len(out) == 0:
                    self.raise_exception(msg)
                break
        self.log_debug('{}.read({}) -> {}'.format(self.__class__.__name__, size, out))
        return out.decode(self.encoding)
