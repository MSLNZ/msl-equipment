"""
Base classes for equipment that is connected through a socket.
"""
import time
import socket

from .connection_message_based import ConnectionMessageBased
from .constants import (
    REGEX_SOCKET,
    REGEX_PROLOGIX,
)


class ConnectionSocket(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a socket.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a socket connection supports the following key-value pairs in the
        :ref:`connections-database` (see also :class:`~socket.socket` for more details)::

            'buffer_size': int, the maximum number of bytes to read at a time [default: 4096]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'family': str, the address family, e.g., 'INET', 'INET6', 'IPX' [default: 'INET']
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
            'proto': int, the socket protocol number [default: 0]
            'read_termination': str or None, read until this termination sequence is found [default: '\\n']
            'rstrip': bool, whether to remove trailing whitespace from "read" messages [default: False]
            'socket_type': str, the socket type, e.g. 'STREAM', 'DGRAM' [default: 'STREAM']
            'termination': shortcut for setting both 'read_termination' and 'write_termination' to this value
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]
            'write_termination': str or None, termination sequence appended to write messages [default: '\\r\\n']

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
        self._socket = None
        super(ConnectionSocket, self).__init__(record)

        self._byte_buffer = bytearray()

        # TODO consider using the `select` module for asynchronous I/O behaviour

        props = record.connection.properties

        self._buffer_size = props.get('buffer_size', 4096)

        if 'family' in props:
            family = props['family'].upper()
            if not family.startswith('AF_'):
                family = 'AF_' + family
            self._family = getattr(socket, family)
        else:
            self._family = socket.AF_INET

        if 'socket_type' in props:
            typ = props['socket_type'].upper()
            if not typ.startswith('SOCK_'):
                typ = 'SOCK_' + typ
            self._type = getattr(socket, typ)
        else:
            self._type = socket.SOCK_STREAM

        self._is_stream = self._type == socket.SOCK_STREAM

        self._proto = props.get('proto', 0)

        info = ConnectionSocket.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))
        self._host, self._port = info['host'], info['port']

        self._connect()
        self.log_debug('Connected to %s', record.connection)

    def _connect(self):
        # it is useful to make this method because some subclasses needed to a "reconnect"
        # because, perhaps, the equipment closed the socket (e.g., OMEGA iTHX)
        if self._socket is not None:
            self._socket.close()

        self._socket = socket.socket(family=self._family, type=self._type, proto=self._proto)
        # in general, it is recommended to set the timeout before calling connect()
        self.timeout = self._timeout

        err_msg = None

        if self._is_stream:
            try:
                self._socket.connect((self._host, self._port))
            except socket.timeout:
                pass
            except socket.error as e:
                err_msg = e.__class__.__name__ + ': ' + str(e)
            else:
                return
        else:
            return

        if err_msg is None:
            self.raise_timeout()
        self.raise_exception('Cannot connect to {}\n{}'.format(self.equipment_record, err_msg))

    def _set_backend_timeout(self):
        if self._socket is not None:
            self._socket.settimeout(self._timeout)

    @property
    def byte_buffer(self):
        """:class:`bytearray`: Returns the reference to the byte buffer."""
        return self._byte_buffer

    @property
    def host(self):
        """:class:`str`: The host (IP address)."""
        return self._host

    @property
    def port(self):
        """:class:`int`: The port number."""
        return self._port

    @property
    def socket(self):
        """:class:`~socket.socket`: The reference to the socket."""
        return self._socket

    @staticmethod
    def parse_address(address):
        """Get the host and port from an address.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            The value of the host and the port or :data:`None` if `address`
            is not valid for a socket.
        """
        match = REGEX_SOCKET.match(address)
        if match:
            d = match.groupdict()

            # if in the IVI format then make sure that `address` is valid`
            if d['prefix'].startswith('TCPIP') and not d['suffix'] == '::SOCKET':
                return

            return {'host': d['host'], 'port': int(d['port'])}

        match = REGEX_PROLOGIX.match(address)
        if match:
            d = match.groupdict()
            return ConnectionSocket.parse_address('TCP::' + d['name'] + d['port'])

    def disconnect(self):
        """Close the socket."""
        if self._socket is not None:
            self._socket.close()
            self.log_debug('Disconnected from %s', self.equipment_record.connection)
            self._socket = None

    def _read(self, size):
        """Overrides method in ConnectionMessageBased."""
        t0 = time.time()
        original_timeout = self._socket.gettimeout()
        while True:

            if size is not None:
                if len(self._byte_buffer) >= size:
                    msg = self._byte_buffer[:size]
                    self._byte_buffer = self._byte_buffer[size:]
                    break

            elif self._read_termination:
                index = self._byte_buffer.find(self._read_termination)
                if index != -1:
                    index += len(self._read_termination)
                    msg = self._byte_buffer[:index]
                    self._byte_buffer = self._byte_buffer[index:]
                    break

            try:
                if self._is_stream:
                    data = self._socket.recv(self._buffer_size)
                else:
                    data, _ = self._socket.recvfrom(self._buffer_size)
            except:
                self._socket.settimeout(original_timeout)
                raise
            else:
                self._byte_buffer.extend(data)

            if len(self._byte_buffer) > self._max_read_size:
                self._socket.settimeout(original_timeout)
                raise RuntimeError('len(message) [{}] > max_read_size [{}]'.format(
                    len(self._byte_buffer), self._max_read_size)
                )

            elapsed_time = time.time() - t0
            if self._timeout and (elapsed_time > self._timeout):
                self._socket.settimeout(original_timeout)
                self.raise_timeout()

            # decrease the timeout when reading each chunk so that the total
            # time to receive all data preserves what was specified
            if original_timeout is not None:
                self._socket.settimeout(max(0, original_timeout - elapsed_time))

        self._socket.settimeout(original_timeout)
        return msg

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

    def _write(self, message):
        """Overrides method in ConnectionMessageBased."""
        if self._is_stream:
            self._socket.sendall(message)
        else:
            self._socket.sendto(message, (self._host, self._port))
        return len(message)
