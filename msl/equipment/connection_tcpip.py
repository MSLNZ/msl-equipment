"""
Base classes for equipment that is connected through TCP/IP.
"""
import time
import socket

from .connection_message_based import ConnectionMessageBased


class ConnectionTCPIPSocket(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that is connected through a TCP/IP socket.

        The :obj:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a TCP/IP Socket connection supports the following key-value pairs in the
        :ref:`connection_database` (see also :class:`socket.socket` for more details)::

            'read_termination': str or None (e.g., "\\r\\n")
            'write_termination': str or None (e.g., "\\n")
            'max_read_size': int (the maximum number of bytes to be read, must be > 0)
            'encoding': str (e.g., 'ascii')
            'timeout': int, float or None (in seconds, default is None)
            'family': str (the address family, default is 'AF_INET')
            'type': str (the socket type, default is 'SOCK_STREAM')
            'buffer_size': int (the number of bytes to read at a time, default is 4096)

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
            If the socket cannot be opened.
        """
        ConnectionMessageBased.__init__(self, record)

        self._socket = None
        self._byte_buffer = bytearray()

        # TODO consider using the `select` module for asynchronous I/O behaviour

        props = record.connection.properties

        self.read_termination = props.get('read_termination', self.read_termination)
        self.write_termination = props.get('write_termination', self.write_termination)
        self.max_read_size = props.get('max_read_size', self.max_read_size)
        self.encoding = props.get('encoding', self.encoding)
        self._buffer_size = props.get('buffer_size', 4096)

        self._set_timeout_value(props.get('timeout', None))

        self._family = getattr(socket, props.get('family', 'AF_INET'))
        self._type = getattr(socket, props.get('type', 'SOCK_STREAM'))

        items = record.connection.address.split('::')
        assert (len(items) == 4) and (items[3].upper() == 'SOCKET'), 'Invalid address ' + record.connection.addres
        self._ip_address = items[1]
        self._port = int(items[2])

        self._connect()
        self.log_debug('Connected to {} '.format(record.connection))

    def _connect(self):
        # it is useful to make this method because some subclasses needed to a "reconnect"
        # because, perhaps, the equipment closed the socket (e.g., OMEGA iTHX)
        if self._socket is not None:
            self._socket.close()

        self._socket = socket.socket(family=self._family, type=self._type)
        # in general it is recommended to call settimeout() before calling connect()
        self.timeout = self._timeout

        err_msg = None

        try:
            self._socket.connect((self._ip_address, self._port))
        except socket.timeout:
            pass
        except socket.error as e:
            err_msg = e.__class__.__name__ + ': ' + str(e)
        else:
            return

        if err_msg is None:
            self.raise_timeout()
        self.raise_exception('Cannot connect to {}\n{}'.format(self.equipment_record, err_msg))

    @property
    def address(self):
        """:class:`str`: The IP address."""
        return self._ip_address

    @property
    def byte_buffer(self):
        """:class:`bytearray`: Returns the reference to the byte buffer."""
        return self._byte_buffer

    @property
    def port(self):
        """:class:`int`: The port number."""
        return self._port

    @property
    def socket(self):
        """:class:`socket.socket`: The reference to the socket."""
        return self._socket

    @ConnectionMessageBased.timeout.setter
    def timeout(self, seconds):
        self._set_timeout_value(seconds)
        self._socket.settimeout(self._timeout)

    def disconnect(self):
        """Close the socket."""
        if self._socket is not None:
            self._socket.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._socket = None

    def write(self, message):
        """Write the given message over the socket.

        Parameters
        ----------
        message : :class:`str`
            The message to write.

        Returns
        -------
        :class:`int`
            The number of bytes sent over the socket.
        """
        data = self._prepare_write(message)

        timeout_error = False
        try:
            self._socket.sendall(data)
        except socket.timeout:
            timeout_error = True  # want to raise MSLTimeoutError not socket.timeout

        if timeout_error:
            self.raise_timeout()

        return len(data)

    def read(self, size=None):
        """Read bytes from the socket.

        Parameters
        ----------
        size : :class:`int` or :obj:`None`, optional
            The number of bytes to read. If `size` is :obj:`None` then read until:

            1. the :attr:`.read_termination` characters are read
               (only if the termination value is not :obj:`None`)
            2. :attr:`.max_read_size` bytes have been read
               (if occurs, raises :exc:`~msl.equipment.exceptions.MSLConnectionError`)
            3. a :exc:`~msl.equipment.exceptions.MSLTimeoutError` occurs
               (only if a :attr:`.timeout` value has been set)

            This method will block until at least one of the above conditions is fulfilled.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        if size and size > self.max_read_size:
            self.raise_exception('max_read_size is {} bytes, requesting {} bytes'.format(
                self.max_read_size, size)
            )

        t0 = time.time()
        timeout_error = False
        while True:

            if size:
                if len(self._byte_buffer) >= size:
                    out = self._byte_buffer[:size]
                    self._byte_buffer = self._byte_buffer[size:]
                    break

            elif self.read_termination:
                index = self._byte_buffer.find(self.read_termination)
                if not index == -1:
                    out = self._byte_buffer[:index]
                    index += len(self.read_termination)
                    self._byte_buffer = self._byte_buffer[index:]
                    break

            try:
                self._byte_buffer.extend(self._socket.recv(self._buffer_size))
            except socket.timeout:
                timeout_error = True  # want to raise MSLTimeoutError not socket.timeout

            if len(self._byte_buffer) > self.max_read_size:
                self.raise_exception('len(byte_buffer) [{}] > max_read_size [{}]'.format(
                    len(self._byte_buffer), self.max_read_size)
                )

            if timeout_error or (self.timeout and (time.time() - t0 > self.timeout)):
                self.raise_timeout()

        self.log_debug('{}.read({!r}) -> {!r}'.format(self, size, out))
        return out.decode(self.encoding)
