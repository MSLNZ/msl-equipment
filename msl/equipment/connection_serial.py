"""
Base class for equipment that is connected through a Serial port.
"""
import re
import time
import serial

from msl.equipment import constants
from msl.equipment.connection_msl import ConnectionMessageBased


class ConnectionSerial(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a Serial port.

        The :obj:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a Serial connection supports the following key-value pairs in the
        :ref:`connection_database` (see also :class:`serial.Serial` for more details about each parameter)::

            'read_termination': str or None (e.g., "\\r\\n")
            'write_termination': str or None (e.g., "\\n")
            'read_size': int (the number of bytes to be read, must be > 0)
            'encoding': str (e.g., 'ascii')
            'baud_rate': int (e.g., 9600, 115200)
            'data_bits': int (e.g., 5, 6, 7, 8)
            'stop_bits': int or float (e.g., 1, 1.5, 2)
            'parity': str (e.g., none, even, odd, mark, space)
            'timeout': float or None (the read timeout value)
            'write_timeout': float or None (the write timeout value)
            'inter_byte_timeout': float or None (the inter-character timeout)
            'exclusive': bool (enable exclusive access mode, for POSIX only)
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
        self.max_read_size = props.get('read_size', self.max_read_size)
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
        """:class:`serial.Serial`: The reference to the Serial object."""
        return self._serial

    @property
    def baud_rate(self):
        """:class:`int`: The baud rate setting."""
        return self._serial.baudrate

    @property
    def data_bits(self):
        """:class:`~.constants.DataBits`: The number of data bits."""
        return constants.DataBits(self._serial.bytesize)

    @property
    def stop_bits(self):
        """:class:`~.constants.StopBits`: The stop bit setting."""
        return constants.StopBits(self._serial.stopbits)

    @property
    def parity(self):
        """:class:`~.constants.Parity`: The parity setting."""
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
        message : :class:`str`
            The message to write.

        Returns
        -------
        :class:`int`:
            The number of bytes written to the Serial port.
        """
        if self.write_termination is not None and not message.endswith(self.write_termination):
            message += self.write_termination
        data = message.encode(self.encoding)
        self.log_debug('{}.write({})'.format(self.__class__.__name__, data))
        return self._serial.write(data)

    def read(self, size=None):
        """Read `size` bytes from the Serial port.

        Trailing whitespace is stripped from the response.

        Parameters
        ----------
        size : :class:`int`
            The number of bytes to read. If `size` is :obj:`None` then read until:

            1. the :obj:`.read_termination` characters are read (only if the termination value is not :obj:`None`)
            2. :obj:`.max_read_size` bytes have been read
            3. a :obj:`timeout` occurs (if a :obj:`timeout` value has been set)

            This method will block until at least one of the above conditions is fulfilled.

        Returns
        -------
        :class:`str`:
            The response from the equipment.

        Raises
        ------
        :exc:`~msl.equipment.exceptions.MSLTimeoutError`
            If a timeout occurs.
        """
        term = None if self.read_termination is None else self.read_termination.encode(self.encoding)
        if size is not None:
            out = self._serial.read(size)
            if len(out) != size:
                self.raise_timeout('received {} bytes, requested {} bytes'.format(len(out), size))
        elif term is not None and term.endswith(serial.LF):
            out = self._serial.readline()
            if not out.endswith(serial.LF):
                self.raise_timeout('did not read a {!r} character'.format(serial.LF))
        else:
            out = bytes()
            start = time.time()
            while True:
                b = self._serial.read(1)
                out += b
                if term is not None and out.endswith(term):
                    break
                if len(out) == self.max_read_size:
                    msg = '{!r}.read() maximum number of bytes read [{}], {} bytes are in the buffer'
                    self.log_warning(msg.format(self, len(out), self._serial.in_waiting))
                    break
                if self.timeout is not None and time.time() - start >= self.timeout:
                    self.raise_timeout()
        self.log_debug('{!r}.read({}) -> {}'.format(self, size, out))
        return out.decode(self.encoding).rstrip()
