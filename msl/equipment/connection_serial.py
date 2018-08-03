"""
Base class for equipment that is connected through a serial port.
"""
import re
import time

import serial

from . import constants
from .connection_message_based import ConnectionMessageBased


class ConnectionSerial(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a serial port.

        The :obj:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a serial connection supports the following key-value pairs in the
        :ref:`connection_database` (see also :class:`serial.Serial` for more details about each parameter)::

            'read_termination': str or None, read until this termination sequence is found [default: '\\n']
            'write_termination': str or None, termination sequence appended to write messages [default: '\\r\\n']
            'termination': shortcut for setting both 'read_termination' and 'write_termination' to this value
            'max_read_size': int, the maximum number of bytes that can be read [default: 2**16]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]
            'baud_rate': int, the baud rate [default: 9600]
            'parity': str or None, parity checking, e.g. 'even', 'odd' [default: None]
            'data_bits': int, the number of data bits, e.g. 5, 6, 7, 8 [default: 8]
            'stop_bits': int or float, the number of stop bits, e.g. 1, 1.5, 2 [default: 1]
            'inter_byte_timeout': float or None, the inter-character timeout [default: None]
            'dsr_dtr': bool, enable hardware (DSR/DTR) flow control [default: False]
            'rts_cts': bool, enable hardware (RTS/CTS) flow control [default: False]
            'xon_xoff': bool, enable software flow control [default: False]

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
            If the serial port cannot be opened.
        """
        ConnectionMessageBased.__init__(self, record)

        self._serial = serial.Serial()

        props = record.connection.properties

        try:
            termination = props['termination']
        except KeyError:
            self.read_termination = props.get('read_termination', self._read_termination)
            self.write_termination = props.get('write_termination', self._write_termination)
        else:
            self.read_termination = termination
            self.write_termination = termination

        self.encoding = props.get('encoding', self._encoding)
        self._encoding_errors = props.get('encoding_errors', self._encoding_errors)
        self.max_read_size = props.get('max_read_size', self._max_read_size)
        self.timeout = props.get('timeout', None)

        if record.connection.address.startswith('SERIAL::'):
            # for addresses like -> SERIAL::/dev/pts/12
            self._serial.port = record.connection.address.split('::')[-1]
        else:
            self._serial.port = record.connection.address

        self._serial.parity = props.get('parity', constants.Parity.NONE).value
        self._serial.inter_byte_timeout = props.get('inter_byte_timeout', None)

        try:
            self._serial.baudrate = props['baud_rate']
        except KeyError:
            self._serial.baudrate = props.get('baudrate', 9600)

        try:
            self._serial.bytesize = props['data_bits']
        except KeyError:
            self._serial.bytesize = props.get('bytesize', constants.DataBits.EIGHT).value

        try:
            self._serial.stopbits = props['stop_bits'].value
        except KeyError:
            self._serial.stopbits = props.get('stopbits', constants.StopBits.ONE).value

        try:
            self._serial.xonxoff = props['xon_xoff']
        except KeyError:
            self._serial.xonxoff = props.get('xonxoff', False)

        try:
            self._serial.rtscts = props['rts_cts']
        except KeyError:
            self._serial.rtscts = props.get('rtscts', False)

        try:
            self._serial.dsrdtr = props['dsr_dtr']
        except KeyError:
            self._serial.dsrdtr = props.get('dsrdtr', False)

        error_msg = ''
        try:
            self._serial.open()
        except serial.serialutil.SerialException:
            # PyVISA and PyVISA-py accept various resource names: 'ASRL#', 'COM#', 'LPT#', 'ASRLCOM#'
            # but Serial seems to only be happy with 'COM#'
            number = re.search('\d+', record.connection.address)  # get the port number from the address
            if number is None:
                self.raise_exception('A port number was not specified -- address={}'.format(record.connection.address))
            self._serial.port = 'COM{}'.format(number.group(0))

            try:
                self._serial.open()
            except serial.serialutil.SerialException as e:
                error_msg = str(e)

        if error_msg:
            self.raise_exception(error_msg)

        self.log_debug('Connected to {}'.format(record.connection))

    @property
    def serial(self):
        """:class:`serial.Serial`: The reference to the serial object."""
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
        self._set_timeout_value(seconds)
        self._serial.timeout = self._timeout
        self._serial.write_timeout = self._timeout

    def disconnect(self):
        """Close the serial port."""
        try:
            # if the subclass raised an error in the constructor before
            # the this class is initialized then self._serial won't exist
            self._serial.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
        except AttributeError:
            pass

    def write(self, message):
        """Write a message over the serial port.

        Parameters
        ----------
        message : :class:`str`
            The message to write.

        Returns
        -------
        :class:`int`
            The number of bytes sent over the serial port.
        """
        data = self._encode(message)
        return self._serial.write(data)

    def read(self, size=None):
        """Read a message from the serial port.

        Parameters
        ----------
        size : :class:`int` or :obj:`None`, optional
            The number of bytes to read. If `size` is :obj:`None` then read until:

            1. :attr:`.read_termination` characters are read
               (only if :attr:`.read_termination` is not :obj:`None`)
            2. :attr:`.max_read_size` bytes have been read
               (raises :exc:`~msl.equipment.exceptions.MSLConnectionError` if occurs)
            3. :exc:`~msl.equipment.exceptions.MSLTimeoutError` occurs
               (only if :attr:`.timeout` is not :obj:`None`)

            This method will block until at least one of the above conditions is fulfilled.

        Returns
        -------
        :class:`str`
            The message from the serial port.
        """
        if size:
            if size > self._max_read_size:
                self.raise_exception('max_read_size is {} bytes, requesting {} bytes'.format(
                    self._max_read_size, size)
                )

            out = self._serial.read(size)
            if len(out) != size:
                self.raise_exception('received {} bytes, requested {} bytes'.format(len(out), size))

        else:
            t0 = time.time()
            out = bytearray()
            while True:
                out.extend(self._serial.read(1))

                if self._read_termination and out.endswith(self._read_termination):
                    out = out[:-len(self._read_termination)]
                    break

                if len(out) > self._max_read_size:
                    self.raise_exception('len(bytes_read) [{}] > max_read_size [{}]'.format(
                        len(out), self._max_read_size)
                    )

                if self._timeout and time.time() - t0 >= self._timeout:
                    self.raise_timeout()

        return self._decode(size, out)
