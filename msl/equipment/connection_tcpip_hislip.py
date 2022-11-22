"""
Base class for equipment that use the HiSLIP communication protocol.
"""
import socket

from .connection_message_based import ConnectionMessageBased
from .constants import REGEX_TCPIP
from .hislip import AsyncClient
from .hislip import FatalErrorMessage
from .hislip import HiSLIPException
from .hislip import PORT
from .hislip import SyncClient


class ConnectionTCPIPHiSLIP(ConnectionMessageBased):

    def __init__(self, record):
        """Base class for equipment that use the HiSLIP communication protocol.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a HiSLIP connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'buffer_size': int, the maximum number of bytes to read at a time [default: 4096]
            'encoding': str, the encoding to use [default: 'utf-8']
            'encoding_errors': str, encoding error handling scheme, e.g. 'strict', 'ignore' [default: 'strict']
            'lock_timeout': float or None, the timeout (in seconds) to wait for a lock [default: 0]
            'max_read_size': int, the maximum number of bytes that can be read [default: 1 MB]
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
        """
        # the following must be defined before calling super()
        self._sync = None
        self._async = None
        super(ConnectionTCPIPHiSLIP, self).__init__(record)

        info = self.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))

        # the board number is currently not used
        self._host = info['host']
        self._name = info['name']
        self._port = info['port']

        # HiSLIP does not support termination characters
        self.write_termination = None
        self.read_termination = None

        props = record.connection.properties
        self._buffer_size = props.get('buffer_size', 4096)
        self.lock_timeout = props.get('lock_timeout', 0)

        self._maximum_server_message_size = None

        self._connect()
        self.log_debug('Connected to %s', record.connection)

    def _connect(self):
        # it is useful to make this method because some subclasses needed to "reconnect"
        err_msg = None

        try:
            # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
            # 23 April 2020 (Revision 2.0)
            # Section 6.1: Initialization Transaction
            self._sync = SyncClient(self._host)
            self._sync.connect(port=self._port, timeout=self._timeout)

            status = self._sync.initialize(sub_address=self._name.encode())
            if status.encrypted or status.initial_encryption:
                self.disconnect()
                raise RuntimeError('The HiSLIP server requires encryption, '
                                   'this has not been tested yet')

            self._async = AsyncClient(self._host)
            self._async.connect(port=self._port, timeout=self._timeout)
            self._async.async_initialize(status.session_id)

            r = self._async.async_maximum_message_size(self._max_read_size)
            self._sync.maximum_server_message_size = r.maximum_message_size
            self._async.maximum_server_message_size = r.maximum_message_size
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
        """Overrides method in ConnectionMessageBased."""
        if self._sync is not None:
            self._sync.set_timeout(self._timeout)
        if self._async is not None:
            self._async.set_timeout(self._timeout)

    @property
    def host(self):
        """:class:`str`: The host (IP address)."""
        return self._host

    @property
    def port(self):
        """:class:`int`: The port number."""
        return self._port

    @property
    def asynchronous(self):
        """:class:`~msl.equipment.hislip.AsyncClient`: The reference to the asynchronous client."""
        return self._async

    @property
    def synchronous(self):
        """:class:`~msl.equipment.hislip.SyncClient`: The reference to the synchronous client."""
        return self._sync

    @staticmethod
    def parse_address(address):
        """Parse the address for valid TCPIP HiSLIP fields.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            The board number, hostname, LAN device name, and HiSLIP port number
            of the device or :data:`None` if `address` is not valid for a TCPIP
            HiSLIP connection.
        """
        match = REGEX_TCPIP.match(address)
        if not match:
            return

        d = match.groupdict()
        if not d['name'] or not d['name'].lower().startswith('hislip'):
            return

        if not d['board']:
            d['board'] = '0'

        name_split = d['name'].split(',')
        if len(name_split) > 1:
            d['name'] = name_split[0]
            try:
                d['port'] = int(name_split[1])
            except ValueError:
                return
        else:
            d['port'] = PORT

        return d

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be
        :meth:`~msl.equipment.connection_message_based.ConnectionMessageBased.read`."""
        # Overrides property in ConnectionMessageBased.
        return self._max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        self._max_read_size = int(size)
        if self._sync is None or self._async is None:
            return

        r = self._async.async_maximum_message_size(self._max_read_size)
        self._sync.maximum_server_message_size = r.maximum_message_size
        self._async.maximum_server_message_size = r.maximum_message_size

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

    def disconnect(self):
        """Close the connection to the HiSLIP server."""
        if self._async is not None:
            self._async.close()
            self._async = None
        if self._sync is not None:
            self._sync.close()
            self._sync = None
        self.log_debug('Disconnected from %s', self.equipment_record.connection)

    def _read(self, size):
        """Overrides method in ConnectionMessageBased."""
        try:
            return self._sync.receive(size=size, max_size=self._max_read_size,
                                      chunk_size=self._buffer_size)
        except HiSLIPException as e:
            # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
            # 23 April 2020 (Revision 2.0)
            # Section 6.2: Fatal Error Detection and Synchronization Recovery
            # If the error is detected by the client, after sending the FatalError
            # messages it shall close the HiSLIP connection
            self._send_fatal_error(e.message)
            raise
        except Exception as e:
            msg = FatalErrorMessage(payload=str(e).encode('ascii'))
            self._send_fatal_error(msg)
            raise

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

    def _send_fatal_error(self, message):
        # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
        # 23 April 2020 (Revision 2.0)
        # Section 6.2: Fatal Error Detection and Synchronization Recovery
        # If the error is detected by the client, after sending the FatalError
        # messages it shall close the HiSLIP connection
        self._sync.write(message)
        self._async.write(message)
        self.disconnect()

    def _write(self, message):
        """Overrides method in ConnectionMessageBased."""
        try:
            return self._sync.send(message)
        except HiSLIPException as e:
            self._send_fatal_error(e.message)
            raise
        except Exception as e:
            msg = FatalErrorMessage(payload=str(e).encode('ascii'))
            self._send_fatal_error(msg)
            raise

    def read_stb(self):
        """Read the status byte from the device.

        Returns
        -------
        :class:`int`
            The status byte.
        """
        reply = self._async.async_status_query(self._sync)
        return reply.status

    def trigger(self):
        """Send the trigger message (emulates a GPIB Group Execute Trigger event)."""
        self._sync.trigger()

    def clear(self):
        """Send the `clear` command to the device."""
        # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
        # 23 April 2020 (Revision 2.0)
        # Section 6.12: Device Clear Transaction
        #
        # This Connection class does not use the asynchronous client in an
        # asynchronous manner, therefore there should not be any pending
        # requests that need to be waited on to finish
        acknowledged = self._async.async_device_clear()
        self._sync.device_clear_complete(acknowledged.feature_bitmap)

    def lock(self, lock_string=''):
        """Acquire the device's lock.

        Parameters
        ----------
        lock_string : :class:`str`, optional
            An ASCII string that identifies this lock. If not specified, then
            an exclusive lock is requested, otherwise the string indicates an
            identification of a shared-lock request.

        Returns
        -------
        :class:`bool`
            Whether acquiring the lock was successful.
        """
        status = self._async.async_lock_request(
            timeout=self._lock_timeout, lock_string=lock_string)
        return status.success

    def unlock(self):
        """Release the lock acquired by :meth:`.lock`.

        Returns
        -------
        :class:`bool`
            Whether releasing the lock was successful.
        """
        status = self._async.async_lock_release(self._sync.message_id)
        return status.success

    def lock_status(self):
        """Request the lock status from the HiSLIP server.

        Returns
        -------
        :class:`bool`
            Whether the HiSLIP server has an exclusive lock with a client.
        :class:`int`
            The number of HiSLIP clients that have a lock with the HiSLIP server.
        """
        reply = self._async.async_lock_info()
        return reply.is_exclusive, reply.num_locks

    def remote_local_control(self, request):
        """Send a GPIB-like remote/local control request.

        Parameters
        ----------
        request : :class:`int`
            The request to perform.

            * 0 -- Disable remote, `VI_GPIB_REN_DEASSERT`
            * 1 -- Enable remote, `VI_GPIB_REN_ASSERT`
            * 2 -- Disable remote and go to local, `VI_GPIB_REN_DEASSERT_GTL`
            * 3 -- Enable Remote and go to remote, `VI_GPIB_REN_ASSERT_ADDRESS`
            * 4 -- Enable remote and lock out local, `VI_GPIB_REN_ASSERT_LLO`
            * 5 -- Enable remote, go to remote, and set local lockout, `VI_GPIB_REN_ASSERT_ADDRESS_LLO`
            * 6 -- go to local without changing REN or lockout state, `VI_GPIB_REN_ADDRESS_GTL`
        """
        self._async.async_remote_local_control(request, self._sync.message_id)
