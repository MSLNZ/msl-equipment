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

            'baud_rate': int, the baud rate [default: 9600]
            'data_bits': int, the number of data bits, e.g. 5, 6, 7, 8 [default: 8]
            'dsr_dtr': bool, enable hardware (DSR/DTR) flow control [default: False]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'inter_byte_timeout': float or None, the inter-character timeout [default: None]
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
            'parity': str or None, parity checking, e.g. 'even', 'odd' [default: None]
            'read_termination': str or None, read until this termination sequence is found [default: '\\n']
            'rstrip': bool, whether to remove trailing whitespace from "read" messages [default: False]
            'rts_cts': bool, enable hardware (RTS/CTS) flow control [default: False]
            'stop_bits': int or float, the number of stop bits, e.g. 1, 1.5, 2 [default: 1]
            'termination': shortcut for setting both 'read_termination' and 'write_termination' to this value
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]
            'write_termination': str or None, termination sequence appended to write messages [default: '\\r\\n']
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
            # this class is initialized then self._serial won't exist
            if self._serial.is_open:
                self._serial.close()
                self.log_debug('Disconnected from %s', self.equipment_record.connection)
        except AttributeError:
            pass

    def _write(self, message):
        """Overrides method in ConnectionMessageBased."""
        return self._serial.write(message)

    def _read(self, size):
        """Overrides method in ConnectionMessageBased."""
        if size is not None:
            return self._serial.read(size)

        msg = bytearray()
        now = time.time
        read = self._serial.read
        r_term = self._read_termination
        timeout = self._timeout
        max_read_size = self._max_read_size
        t0 = now()
        while True:
            msg.extend(read(1))

            if r_term and msg.endswith(r_term):
                return msg

            if len(msg) > max_read_size:
                raise RuntimeError('len(message) [{}] > max_read_size [{}]'.format(
                    len(msg), max_read_size))

            if timeout and now() - t0 > timeout:
                self.raise_timeout()

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
