"""
Base class for equipment that is connected through a serial port.
"""
import time

import serial

from .connection_message_based import ConnectionMessageBased
from .constants import (
    Parity,
    StopBits,
    DataBits,
    REGEX_SERIAL,
    REGEX_PROLOGIX,
)


class ConnectionSerial(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a serial port.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a serial connection supports the following key-value pairs in the
        :ref:`connections-database` (see also :class:`serial.Serial` for more
        details about each parameter)::

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

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by
        setting the value in the **Backend** field for a connection record
        in the :ref:`connections-database` to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.

        Raises
        ------
        ~msl.equipment.exceptions.MSLConnectionError
            If the serial port cannot be opened.
        """
        self._serial = serial.Serial()
        super(ConnectionSerial, self).__init__(record)

        info = ConnectionSerial.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))
        self._serial.port = info['port']

        props = record.connection.properties
        self._serial.parity = props.get('parity', Parity.NONE).value
        self._serial.inter_byte_timeout = props.get('inter_byte_timeout', None)

        try:
            self._serial.baudrate = props['baud_rate']
        except KeyError:
            self._serial.baudrate = props.get('baudrate', 9600)

        try:
            self._serial.bytesize = props['data_bits'].value
        except KeyError:
            self._serial.bytesize = props.get('bytesize', DataBits.EIGHT).value

        try:
            self._serial.stopbits = props['stop_bits'].value
        except KeyError:
            self._serial.stopbits = props.get('stopbits', StopBits.ONE).value

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

        try:
            self._serial.open()
        except serial.serialutil.SerialException as err:
            # don't raise SerialException, use self.raise_exception below
            error_msg = str(err)
        else:
            error_msg = None

        if error_msg:
            self.raise_exception(error_msg)

        self.log_debug('Connected to %s', record.connection)

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
        return DataBits(self._serial.bytesize)

    @property
    def stop_bits(self):
        """:class:`~.constants.StopBits`: The stop bit setting."""
        return StopBits(self._serial.stopbits)

    @property
    def parity(self):
        """:class:`~.constants.Parity`: The parity setting."""
        return Parity(self._serial.parity)

    def _set_backend_timeout(self):
        self._serial.timeout = self._timeout
        self._serial.write_timeout = self._timeout

    def disconnect(self):
        """Close the serial port."""
        try:
            # if the subclass raised an error in the constructor before
            # the this class is initialized then self._serial won't exist
            if self._serial.is_open:
                self._serial.close()
                self.log_debug('Disconnected from %s', self.equipment_record.connection)
        except AttributeError:
            pass

    def write(self, msg):
        """Write a message over the serial port.

        Parameters
        ----------
        msg : :class:`str`
            The message to write.

        Returns
        -------
        :class:`int`
            The number of bytes sent over the serial port.
        """
        data = self._encode(msg)
        return self._serial.write(data)

    def read(self, size=None):
        """Read a message from the serial port.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read. If `size` is :data:`None` then read until:

            1. :obj:`~msl.equipment.connection_message_based.ConnectionMessageBased.read_termination`
               characters are read (only if
               :obj:`~msl.equipment.connection_message_based.ConnectionMessageBased.read_termination`
               is not :data:`None`)
            2. :obj:`~msl.equipment.connection_message_based.ConnectionMessageBased.max_read_size`
               bytes have been read (raises :exc:`~msl.equipment.exceptions.MSLConnectionError` if occurs)
            3. :exc:`~msl.equipment.exceptions.MSLTimeoutError` occurs
               (only if :obj:`~msl.equipment.connection_message_based.ConnectionMessageBased.timeout`
               is not :data:`None`)

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

    @staticmethod
    def parse_address(address):
        """Get the serial port from an address.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`

        Returns
        -------
        :class:`dict` or :data:`None`
            The serial port in a format that is valid for PySerial (i.e., ``ASRL3`` becomes ``COM3``)
            or :data:`None` if the port cannot be determined from `address`.
        """
        match = REGEX_SERIAL.match(address)
        if match:
            d = match.groupdict()
            prefix = 'COM' if d['dev'] is None else d['dev']
            return {'port': prefix + d['number']}

        match = REGEX_PROLOGIX.match(address)
        if match:
            d = match.groupdict()
            prefix = 'ASRL' if d['name'].startswith('/') else ''
            return ConnectionSerial.parse_address(prefix + d['name'])
