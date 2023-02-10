"""
Base class for equipment that use the ZeroMQ communication protocol.
"""
import socket

import zmq

from .connection_message_based import ConnectionMessageBased
from .constants import REGEX_ZMQ


class ConnectionZeroMQ(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that use the ZeroMQ communication protocol.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a ZeroMQ connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
            'protocol': str, the ZeroMQ protocol [default: 'tcp']
            'rstrip': bool, whether to remove trailing whitespace from "read" messages [default: False]
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by
        setting the value in the **Backend** field for a connection record
        in the :ref:`connections-database` to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment-database`.

        Raises
        ------
        ~msl.equipment.exceptions.MSLConnectionError
            If the socket cannot be opened.
        """
        # the following must be defined before calling super()
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        super(ConnectionZeroMQ, self).__init__(record)

        info = self.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))

        self._host = info['host']
        self._port = info['port']

        # ZeroMQ does not use termination characters
        self.write_termination = None
        self.read_termination = None

        self._protocol = record.connection.properties.get('protocol', 'tcp')

        self._connect()
        self.log_debug('Connected to %s', record.connection)

    def _connect(self):
        err_msg = None
        default_timeout = 10

        # Calling zmq.Socket.connect() does not verify if the connection
        # can be made, so use the builtin socket module to verify
        s = socket.socket()

        try:
            s.settimeout(self.timeout or default_timeout)
            s.connect((self._host, self._port))

            # The (host, port) is valid, so now call zmq.Socket.connect()
            self._socket.connect('{}://{}:{}'.format(self._protocol, self._host, self._port))
        except socket.timeout:
            pass
        except Exception as e:
            err_msg = e.__class__.__name__ + ': ' + str(e)
        else:
            return
        finally:
            s.close()

        if err_msg is None:
            if not self.timeout:
                self.timeout = default_timeout
            self.raise_timeout()
        self.raise_exception('Cannot connect to {}\n{}'.format(self.equipment_record, err_msg))

    def _read(self, size):
        """Overrides method in ConnectionMessageBased."""
        reply = self._socket.recv(flags=0, copy=True)
        if size is None:
            return reply
        return reply[:size]

    def _set_backend_timeout(self):
        """Overrides method in ConnectionMessageBased."""
        # ZeroMQ requires the timeout to be an integer with units of milliseconds
        if self._timeout is None:
            timeout_ms = -1  # infinite
        else:
            timeout_ms = int(self._timeout * 1000)
        self._socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

    def _write(self, message):
        """Overrides method in ConnectionMessageBased."""
        self._socket.send(message, flags=0, copy=True)
        return len(message)

    @property
    def context(self):
        """:class:`~zmq.sugar.context.Context`: Reference to the ZeroMQ context."""
        return self._context

    def disconnect(self):
        """Close the connection."""
        self._context.destroy()
        self.log_debug('Disconnected from %s', self.equipment_record.connection)

    @property
    def host(self):
        """:class:`str`: The host (IP address)."""
        return self._host

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be
        :meth:`~msl.equipment.connection_message_based.ConnectionMessageBased.read`."""
        # Overrides property in ConnectionMessageBased.
        return self._max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        size = int(size)
        if size < 1:
            raise ValueError('The maximum number of bytes to read must be > 0, got {}'.format(size))
        self._max_read_size = size
        self._socket.setsockopt(zmq.MAXMSGSIZE, size)

    @staticmethod
    def parse_address(address):
        """Parse the address for valid ZeroMQ fields.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            The host and port number of the device or :data:`None` if `address`
            is not valid for a ZeroMQ connection.
        """
        match = REGEX_ZMQ.match(address)
        if not match:
            return

        d = match.groupdict()
        return {'host': d['host'], 'port': int(d['port'])}

    @property
    def port(self):
        """:class:`int`: The port number."""
        return self._port

    def reconnect(self, max_attempts=1):
        """Reconnect to the equipment.

        Parameters
        ----------
        max_attempts : :class:`int`, optional
            The maximum number of attempts to try to reconnect with the
            equipment. If < 1 or :data:`None` then keep trying until a
            connection is successful. If the maximum number of attempts
            has been reached then an exception is raise.
        """
        if max_attempts is None:
            max_attempts = -1

        attempt = 0
        while True:
            attempt += 1
            try:
                return self._connect()
            except:
                if 0 < max_attempts <= attempt:
                    raise

    @property
    def socket(self):
        """:class:`~zmq.sugar.socket.Socket`: Reference to the ZeroMQ socket."""
        return self._socket
