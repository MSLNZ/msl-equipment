"""
Base class for equipment that use the VXI-11 communication protocol.
"""
import socket
import time
from struct import Struct

from .connection_message_based import ConnectionMessageBased
from .constants import REGEX_TCPIP
from .vxi11 import AsyncClient
from .vxi11 import CoreClient
from .vxi11 import DEVICE_CORE
from .vxi11 import DEVICE_CORE_VERSION
from .vxi11 import OperationFlag
from .vxi11 import RX_CHR
from .vxi11 import RX_END
from .vxi11 import VXI_ERROR_CODES


class ConnectionTCPIPVXI11(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that use the VXI-11 communication protocol.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a VXI-11 connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'buffer_size': int, the maximum number of bytes to read at a time [default: 4096]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'lock_timeout': float or None, the timeout (in seconds) to wait for a lock [default: 0]
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
            'port': int, the port to use instead of calling the RPC Port Mapper function [default: None]
            'read_termination': str or None, read until this termination character is found [default: None]
            'rstrip': bool, whether to remove trailing whitespace from "read" messages [default: False]
            'termination': alias for 'read_termination'
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
        """
        # the following must be defined before calling super()
        self._core_client = None
        self._abort_client = None
        self._link_id = None
        self._lock_timeout = 0
        super(ConnectionTCPIPVXI11, self).__init__(record)

        info = self.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))

        # the board number is currently not used
        self._host = info['host']
        self._name = info['name']

        props = record.connection.properties
        self._buffer_size = props.get('buffer_size', 4096)
        self.lock_timeout = props.get('lock_timeout', 0)

        self._core_port = props.get('port', None)
        self._abort_port = None
        self._max_recv_size = None

        # A non-empty read_termination value is applied by default in
        # ConnectionMessageBased if the user did not specify one. Set it back
        # to None if a read-termination character was not explicitly specified.
        if 'read_termination' not in props and 'termination' not in props:
            self.read_termination = None

        # VXI-11 does not support write-termination characters
        self.write_termination = None

        self._connect()
        self.log_debug('Connected to %s', record.connection)

    def _connect(self):
        # it is useful to make this method because some subclasses needed to "reconnect"
        err_msg = None

        try:
            if self._core_port is None:
                cc = CoreClient(self._host)
                self._core_port = cc.get_port(
                    DEVICE_CORE, DEVICE_CORE_VERSION,
                    socket.IPPROTO_TCP, timeout=self.timeout)

            self._core_client = CoreClient(self._host)
            self._core_client.connect(self._core_port, timeout=self.timeout)

            params = self._core_client.create_link(self._name, False, self._lock_timeout_ms)
            self._link_id, self._abort_port, max_recv_size = params
            self._max_recv_size = min(max_recv_size, 2 ** 16)
        except socket.timeout:
            pass
        except Exception as e:
            err_msg = e.__class__.__name__ + ': ' + str(e)
        else:
            return

        if err_msg is None:
            self.raise_timeout()
        self.raise_exception('Cannot connect to {}\n{}'.format(self.equipment_record, err_msg))

    def _set_backend_timeout(self):
        # Overrides method in ConnectionMessageBased
        if self._timeout is None:
            # use 1 day as equivalent to a socket in blocking mode
            self._io_timeout_ms = 86400000
        else:
            self._io_timeout_ms = int(self._timeout * 1000)
        self._set_socket_timeout()

    def _set_socket_timeout(self):
        if self._timeout is None:
            # the socket is put in blocking mode
            timeout = None
        else:
            # the socket timeout value must be > io_timeout + lock_timeout
            timeout = 1 + self._timeout + self._lock_timeout

        if self._core_client is not None:
            self._core_client.set_timeout(timeout)

        if self._abort_client is not None:
            self._abort_client.set_timeout(timeout)

    @property
    def byte_buffer(self):
        """:class:`bytearray`: Returns the reference to the byte buffer."""
        if self._core_client is None:
            return bytearray()
        return self._core_client.get_buffer()

    @property
    def host(self):
        """:class:`str`: The host (IP address)."""
        return self._host

    @property
    def port(self):
        """:class:`int`: The port number."""
        return self._core_port

    @property
    def socket(self):
        """:class:`~socket.socket`: The reference to the socket."""
        if self._core_client is None:
            return None
        return self._core_client.socket

    @staticmethod
    def parse_address(address):
        """Parse the address for valid TCPIP VXI-11 fields.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            The board number, hostname, and LAN device name of the device or
            :data:`None` if `address` is not valid for a TCPIP VXI-11 connection.
        """
        match = REGEX_TCPIP.match(address)
        if not match:
            return

        d = match.groupdict()
        if not d['name']:
            d['name'] = 'inst0'
        elif d['name'].lower().startswith('hislip'):
            # the HiSLIP protocol shares a common VISA Resource name syntax
            return

        if not d['board']:
            d['board'] = '0'

        return d

    def disconnect(self):
        """Unlink and close the sockets."""
        if self._abort_client is not None:
            try:
                self._abort_client.close()
            except:
                pass
            finally:
                self._abort_client = None

        if self._link_id is not None:
            try:
                self._core_client.destroy_link(self._link_id)
            except:
                pass
            finally:
                self._link_id = None

        if self._core_client is not None:
            try:
                self._core_client.close()
                self.log_debug('Disconnected from %s', self.equipment_record.connection)
            except Exception as e:
                self.log_error('Could not disconnect from %s\n%s',
                               self.equipment_record.connection, e)
            finally:
                self._core_client = None

    def _read(self, size):
        """Overrides method in ConnectionMessageBased."""
        if size is None:
            request_size = self._buffer_size
        else:
            request_size = min(size, self._buffer_size)

        term_char = 0
        flags = self._init_flag()

        if self._read_termination:
            term_char = ord(self._read_termination)
            flags |= OperationFlag.TERMCHRSET

        now = time.time
        io_timeout = self._io_timeout_ms
        reason = 0
        done_flag = RX_END | RX_CHR
        msg = bytearray()
        t0 = now()
        while reason & done_flag == 0:

            try:
                reason, data = self._core_client.device_read(
                    self._link_id,
                    request_size,
                    io_timeout,
                    self._lock_timeout_ms,
                    flags,
                    term_char
                )
            except Exception as e:
                if VXI_ERROR_CODES[15] in str(e):
                    self.raise_timeout()
                raise
            else:
                msg.extend(data)
                if size is not None:
                    size -= len(data)
                    if size <= 0:
                        break
                    request_size = min(size, self._buffer_size)

            if len(msg) > self._max_read_size:
                raise RuntimeError('len(message) [{}] > max_read_size [{}]'.format(
                    len(msg), self._max_read_size))

            # decrease io_timeout before reading the next chunk so that the
            # total time to receive all data preserves what was specified
            if self._io_timeout_ms > 0:
                io_timeout = max(0, self._io_timeout_ms - int((now() - t0) * 1000))

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
        flags = self._init_flag()
        offset = 0
        num = len(message)
        view = memoryview(message)  # avoids unnecessarily copying of slices
        while num > 0:
            if num <= self._max_recv_size:
                flags |= OperationFlag.END

            block = view[offset:offset+self._max_recv_size]

            try:
                size = self._core_client.device_write(
                    self._link_id,
                    self._io_timeout_ms,
                    self._lock_timeout_ms,
                    flags,
                    block
                )
            except Exception as e:
                if VXI_ERROR_CODES[15] in str(e):
                    raise socket.timeout
                raise
            else:
                if size < len(block):
                    # raise any error, the ConnectionMessageBased class will
                    # handle the exception type
                    raise RuntimeError('The number of bytes written is less than expected')

                offset += size
                num -= size

        return offset

    @property
    def lock_timeout(self):
        """:class:`float`: The time, in seconds, to wait to acquire a lock."""
        return self._lock_timeout

    @lock_timeout.setter
    def lock_timeout(self, value):
        if value is None or value < 0:
            # use 1 day as equivalent to "wait forever for a lock"
            self._lock_timeout = 86400.0
        else:
            self._lock_timeout = float(value)
        self._lock_timeout_ms = int(self._lock_timeout * 1000)
        self._set_socket_timeout()

    def _init_flag(self):
        # initialize the flag
        if self._lock_timeout_ms > 0:
            return OperationFlag.WAITLOCK
        return OperationFlag.NULL

    def abort(self):
        """Stop an in-progress request."""
        if self._abort_client is None:
            self._abort_client = AsyncClient(self.host)
            self._abort_client.connect(self._abort_port, timeout=self.timeout)
        self._abort_client.device_abort(self._link_id)

    def read_stb(self):
        """Read the status byte from the device.

        Returns
        -------
        :class:`int`
            The status byte.
        """
        return self._core_client.device_readstb(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms,
            self._io_timeout_ms
        )

    def trigger(self):
        """Send a trigger to the device."""
        self._core_client.device_trigger(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms,
            self._io_timeout_ms
        )

    def clear(self):
        """Send the `clear` command to the device."""
        self._core_client.device_clear(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms,
            self._io_timeout_ms
        )

    def remote(self):
        """Place the device in a remote state wherein all programmable local
        controls are disabled.
        """
        self._core_client.device_remote(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms,
            self._io_timeout_ms
        )

    def local(self):
        """Place the device in a local state wherein all programmable local
        controls are enabled.
        """
        self._core_client.device_local(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms,
            self._io_timeout_ms
        )

    def lock(self):
        """Acquire the device's lock."""
        self._core_client.device_lock(
            self._link_id,
            self._init_flag(),
            self._lock_timeout_ms
        )

    def unlock(self):
        """Release the lock acquired by :meth:`.lock`"""
        self._core_client.device_unlock(self._link_id)

    def enable_sqr(self, enable, handle):
        """Enable or disable the sending of `device_intr_srq` RPCs by the
        network instrument server.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to enable or disable interrupts.
        handle : :class:`bytes`
            Host specific data (maximum length is 40 characters).
        """
        self._core_client.device_enable_srq(
            self._link_id,
            enable,
            handle
        )

    def docmd(self, cmd, value, fmt):
        """Allows for a variety of commands to be executed.

        Parameters
        ----------
        cmd : :class:`int`
            An IEEE 488 command messages, (e.g., to send a group execute trigger,
            ``GET``, command the value of `cmd` would be 0x08).
        value : :class:`bool`, :class:`int` or :class:`float`
            The value to use with `cmd`.
        fmt : :class:`str`
            How to format `value`. See :ref:`format-characters` for more details.
            Do not include the byte-order character. Network (big-endian) order
            will always be used.

        Returns
        -------
        :class:`bytes`
            The results defined by `cmd`.
        """
        # always use network (big-endian) byte order
        s = Struct('!' + fmt.lstrip('@=<>!'))
        return self._core_client.device_docmd(
            self._link_id,
            self._init_flag(),
            self._io_timeout_ms,
            self._lock_timeout_ms,
            cmd,
            True,  # network byte order
            s.size,
            s.pack(value)
        )

    def destroy_link(self):
        """Destroy the link with the device."""
        self._core_client.destroy_link(self._link_id)

    def create_intr_chan(self, host_addr, host_port, prog_num, prog_vers, prog_family):
        """Inform the network instrument server to establish an interrupt channel.

        Parameters
        ----------
        host_addr : :class:`int`
            Host servicing the interrupt.
        host_port : :class:`int`
            Valid port number on the client.
        prog_num : :class:`int`
            Program number.
        prog_vers : :class:`int`
            Program version number.
        prog_family : :class:`int`
            The underlying socket protocol family type
            (``IPPROTO_TCP`` or ``IPPROTO_UDP``).
        """
        self._core_client.create_intr_chan(
            host_addr,
            host_port,
            prog_num,
            prog_vers,
            prog_family
        )

    def destroy_intr_chan(self):
        """Inform the network instrument server to close its interrupt channel."""
        self._core_client.destroy_intr_chan()
