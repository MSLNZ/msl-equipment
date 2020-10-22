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
        :ref:`connections-database` (see also :func:`socket.socket` for more details)::

            'read_termination': str or None, read until this termination sequence is found [default: '\\n']
            'write_termination': str or None, termination sequence appended to write messages [default: '\\r\\n']
            'termination': shortcut for setting both 'read_termination' and 'write_termination' to this value
            'max_read_size': int, the maximum number of bytes that can be read [default: 2**16]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'timeout': float or None, the timeout (in seconds) for read and write operations [default: None]
            'family': str, the address family, e.g., 'INET', 'INET6', 'IPX' [default: 'INET']
            'socket_type': str, the socket type, e.g. 'STREAM', 'DGRAM' [default: 'STREAM']
            'proto': int, the socket protocol number [default: 0]
            'buffer_size': int, the number of bytes to read at a time [default: 4096]

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
        self.log_debug('Connected to {} '.format(record.connection))

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
        """:func:`socket.socket`: The reference to the socket."""
        return self._socket

    def disconnect(self):
        """Close the socket."""
        if self._socket is not None:
            self._socket.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._socket = None

    def write(self, msg):
        """Write the given message over the socket.

        Parameters
        ----------
        msg : :class:`str`
            The message to write.

        Returns
        -------
        :class:`int`
            The number of bytes sent over the socket.
        """
        data = self._encode(msg)

        timeout_error = False
        try:
            if self._is_stream:
                self._socket.sendall(data)
            else:
                self._socket.sendto(data, (self._host, self._port))
        except socket.timeout:
            timeout_error = True  # want to raise MSLTimeoutError not socket.timeout

        if timeout_error:
            self.raise_timeout()

        return len(data)

    def read(self, size=None):
        """Read a message from the socket.

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
            The message from the socket.
        """
        if size is not None and size > self._max_read_size:
            self.raise_exception('max_read_size is {} bytes, requesting {} bytes'.format(
                self._max_read_size, size)
            )

        t0 = time.time()
        timeout_error = False
        while True:

            if size is not None:
                if len(self._byte_buffer) >= size:
                    out = self._byte_buffer[:size]
                    self._byte_buffer = self._byte_buffer[size:]
                    break

            elif self._read_termination:
                index = self._byte_buffer.find(self._read_termination)
                if not index == -1:
                    out = self._byte_buffer[:index]
                    index += len(self._read_termination)
                    self._byte_buffer = self._byte_buffer[index:]
                    break

            try:
                if self._is_stream:
                    data = self._socket.recv(self._buffer_size)
                else:
                    data, _ = self._socket.recvfrom(self._buffer_size)
            except socket.timeout:
                timeout_error = True  # want to raise MSLTimeoutError not socket.timeout
            else:
                self._byte_buffer.extend(data)

            if len(self._byte_buffer) > self._max_read_size:
                self.raise_exception('len(byte_buffer) [{}] > max_read_size [{}]'.format(
                    len(self._byte_buffer), self._max_read_size)
                )

            if timeout_error or (self._timeout and (time.time() - t0 > self._timeout)):
                self.raise_timeout()

        return self._decode(size, out)

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
