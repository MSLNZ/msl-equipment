"""
Implementation of the HiSLIP_ protocol for a client.

This module implements the following IVI Protocol Specification:

`IVI-6.1: High-Speed LAN Instrument Protocol (HiSLIP) v2.0 April 23, 2020`

.. _HiSLIP: https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf
"""
import socket
import time
from struct import Struct
from struct import pack
from struct import unpack

from enum import IntEnum

PORT = 4880


# Table 4, Section 2.5: Numeric Values of Message Type codes
class MessageType(IntEnum):
    """Message types."""
    Initialize = 0
    InitializeResponse = 1
    FatalError = 2
    Error = 3
    AsyncLock = 4
    AsyncLockResponse = 5
    Data = 6
    DataEnd = 7
    DeviceClearComplete = 8
    DeviceClearAcknowledge = 9
    AsyncRemoteLocalControl = 10
    AsyncRemoteLocalResponse = 11
    Trigger = 12
    Interrupted = 13
    AsyncInterrupted = 14
    AsyncMaximumMessageSize = 15
    AsyncMaximumMessageSizeResponse = 16
    AsyncInitialize = 17
    AsyncInitializeResponse = 18
    AsyncDeviceClear = 19
    AsyncServiceRequest = 20
    AsyncStatusQuery = 21
    AsyncStatusResponse = 22
    AsyncDeviceClearAcknowledge = 23
    AsyncLockInfo = 24
    AsyncLockInfoResponse = 25
    GetDescriptors = 26
    GetDescriptorsResponse = 27
    StartTLS = 28
    AsyncStartTLS = 29
    AsyncStartTLSResponse = 30
    EndTLS = 31
    AsyncEndTLS = 32
    AsyncEndTLSResponse = 33
    GetSaslMechanismList = 34
    GetSaslMechanismListResponse = 35
    AuthenticationStart = 36
    AuthenticationExchange = 37
    AuthenticationResult = 38


class ErrorType(IntEnum):
    """Error types."""
    # Common to both fatal and non-fatal errors
    UNIDENTIFIED = 0

    # Fatal errors (Table 14, Section 6.2)
    BAD_HEADER = 1
    CHANNELS_INACTIVATED = 2
    INVALID_INIT_SEQUENCE = 3
    MAX_CLIENTS = 4

    # Non-fatal errors (Table 16, Section 6.3)
    BAD_MESSAGE_TYPE = 1
    BAD_CONTROL_CODE = 2
    BAD_VENDOR = 3
    MESSAGE_TOO_LARGE = 4
    AUTHENTICATION_FAILED = 5


class HiSLIPException(Exception):
    _mapping = {}  # override in subclass, int -> bytes

    def __init__(self, message_type, control_code, reason=None):
        """Base class for HiSLIP exceptions.

        Parameters
        ----------
        message_type : :class:`MessageType`
            The message type.
        control_code : :class:`int`
            The control code from the server response.
        reason : :class:`str`
            Additional information to display in exception string.
        """
        super(HiSLIPException, self).__init__()
        if control_code not in self._mapping:
            control_code = ErrorType.UNIDENTIFIED
        self.reason = reason
        self._message = Message()
        self._message.type = message_type
        self._message.control_code = control_code
        self._message.payload = self._mapping[control_code]

    @property
    def message(self):
        """:class:`Message`: The error message that can be written to the server."""
        return self._message

    def __str__(self):
        code = self._message.control_code
        text = self._message.payload.decode()
        if self.reason:
            return '{} [code={}, reason={!r}]'.format(text, code, self.reason)
        return '{} [code={}]'.format(text, code)


# Table 14, Section 6.2: Fatal Error Detection and Synchronization Recovery
class FatalError(HiSLIPException):

    _mapping = {
        ErrorType.UNIDENTIFIED: b'Unidentified error',
        ErrorType.BAD_HEADER: b'Poorly formed message header',
        ErrorType.CHANNELS_INACTIVATED: b'Attempt to use connection without both channels established',
        ErrorType.INVALID_INIT_SEQUENCE: b'Invalid initialization sequence',
        ErrorType.MAX_CLIENTS: b'Server refused connection due to maximum number of clients exceeded'
    }

    def __init__(self, control_code, reason=None):
        """Exception for a fatal error.

        Parameters
        ----------
        control_code : :class:`int`
            The control code from the server response.
        reason : :class:`str`
            Additional information to display in exception string.
        """
        super(FatalError, self).__init__(MessageType.FatalError, control_code, reason)


# Table 16, Section 6.3: Error Notification Transaction
class Error(HiSLIPException):

    _mapping = {
        ErrorType.UNIDENTIFIED: b'Unidentified error',
        ErrorType.BAD_MESSAGE_TYPE: b'Unrecognized message type',
        ErrorType.BAD_CONTROL_CODE: b'Unrecognized control code',
        ErrorType.BAD_VENDOR: b'Unrecognized vendor defined message',
        ErrorType.MESSAGE_TOO_LARGE: b'Message too large',
        ErrorType.AUTHENTICATION_FAILED: b'Authentication failed'
    }

    def __init__(self, control_code, reason=None):
        """Exception for a non-fatal error.

        Parameters
        ----------
        control_code : :class:`int`
            The control code from the server response.
        reason : :class:`str`
            Additional information to display in exception string.
        """
        super(Error, self).__init__(MessageType.Error, control_code, reason)


class Message(object):
    header = Struct('!2s2BIQ')
    prologue = b'HS'
    type = None

    def __init__(self, control_code=0, parameter=0, payload=b''):
        """Create a new HiSLIP message.

        Parameters
        ----------
        control_code : :class:`int`, optional
            This 8-bit field is a general parameter for the message. If the
            field is not defined for a message, 0 shall be sent.
        parameter : :class:`int`, optional
            This 32-bit field has various uses in different messages. If this
            field is not defined for a message, 0 shall be sent.
        payload : :class:`bytes`, optional
            The payload data.
        """
        self.control_code = control_code
        self.parameter = parameter
        self.payload = payload

    def __repr__(self):
        typ = None if self.type is None else self.type.name
        if not self.payload:
            payload = "payload=b''"
        elif len(self.payload) < 50:
            payload = 'payload={}'.format(self.payload)
        else:
            payload = 'payload[{}]={}...{}'.format(
                self.length_payload, self.payload[:25], self.payload[-25:])
        return 'Message<type={} control_code={} parameter={} {}>'.format(
                typ, self.control_code, self.parameter, payload)

    @property
    def length_payload(self):
        """:class:`int`: The length of the payload."""
        return len(self.payload)

    def pack(self):
        """Convert the message to bytes.

        Returns
        -------
        :class:`bytearray`
            The messaged packed as bytes.
        """
        data = bytearray(
            self.header.pack(
                self.prologue,
                self.type,
                self.control_code,
                self.parameter,
                self.length_payload
            ))
        data.extend(self.payload)
        return data

    @staticmethod
    def repack(unpack_fmt, pack_fmt, *args):
        """Convert arguments from one byte format to another.

        Parameters
        ----------
        unpack_fmt : :class:`str`
            The format to convert the arguments to.
        pack_fmt : :class:`str`
            The format that the arguments are currently in.
        *args
            The arguments to convert.

        Returns
        -------
        :class:`tuple`
            The converted arguments.
        """
        return unpack(unpack_fmt, pack(pack_fmt, *args))

    @property
    def size(self):
        """:class:`int` The total size of the message."""
        return self.header.size + self.length_payload


class FatalErrorMessage(Message):
    type = MessageType.FatalError


class ErrorMessage(Message):
    type = MessageType.Error


class Initialize(Message):
    type = MessageType.Initialize

    def __init__(self, major, minor, client_id, sub_address):
        """Create an Initialize message.

        Parameters
        ----------
        major : :class:`int`
            The major version number of the HiSLIP protocol that the client
            supports.
        minor : :class:`int`
            The minor version number of the HiSLIP protocol that the client
            supports.
        client_id : :class:`bytes`
            The vendor ID of the client. Must have a length of 2 characters.
        sub_address : :class:`bytes`
            A particular device managed by this server. For VISA clients this
            field corresponds to the VISA LAN device name (default is `hislip0`).
            The maximum length is 256 characters.
        """
        super(Initialize, self).__init__(payload=sub_address)
        self.parameter, = self.repack('!I', '!2B2s', major, minor, client_id)


class InitializeResponse(Message):
    type = MessageType.InitializeResponse

    # Flags from Table 12 (Step 3), Section 6.1: Initialization Transaction
    _OVERLAP_MODE = 1 << 0
    _ENCRYPTION_MODE = 1 << 1
    _INITIAL_ENCRYPTION = 1 << 2

    @property
    def encrypted(self):
        """:class:`bool`: Whether encryption is optional or mandatory."""
        return bool(self.control_code & self._ENCRYPTION_MODE)

    @property
    def initial_encryption(self):
        """:class:`bool`: Whether the client shall switch to encrypted mode."""
        return bool(self.control_code & self._INITIAL_ENCRYPTION)

    @property
    def overlapped(self):
        """:class:`bool`: Whether the server is in overlapped or synchronous mode."""
        return bool(self.control_code & self._OVERLAP_MODE)

    @property
    def protocol_version(self):
        """:class:`tuple`: The (major, minor) version numbers of the HiSLIP
        protocol that the client and server are to use."""
        return self.repack('!2BH', '!I', self.parameter)[:2]

    @property
    def session_id(self):
        """:class:`int`: The session ID."""
        return self.repack('!2BH', '!I', self.parameter)[2]


class Data(Message):
    type = MessageType.Data


class DataEnd(Message):
    type = MessageType.DataEnd


class AsyncLock(Message):
    type = MessageType.AsyncLock


class AsyncLockResponse(Message):
    type = MessageType.AsyncLockResponse

    # Table 19 and 20, Section 6.5: Lock Transaction
    _FAILURE = 0
    _SUCCESS = 1
    _SHARED = 2
    _ERROR = 3

    @property
    def error(self):
        """:class:`bool`: Whether the request was an invalid attempt to release
        a lock that was not acquired or to request a lock already granted."""
        return self.control_code == self._ERROR

    @property
    def failed(self):
        """:class:`bool`: Whether a lock was requested but not granted (timeout expired)."""
        return self.control_code == self._FAILURE

    @property
    def success(self):
        """:class:`bool`: Whether requesting or releasing the lock was successful."""
        return self.control_code == self._SUCCESS or self.control_code == self._SHARED

    @property
    def shared_released(self):
        """:class:`bool`: Whether releasing a shared lock was successful."""
        return self.control_code == self._SHARED


class AsyncLockInfo(Message):
    type = MessageType.AsyncLockInfo


class AsyncLockInfoResponse(Message):
    type = MessageType.AsyncLockInfoResponse

    @property
    def exclusive(self):
        """:class:`bool`: Whether the HiSLIP server has an exclusive lock with a client."""
        return self.control_code == 1

    @property
    def num_locks(self):
        """:class:`int`: The number of HiSLIP clients that have a lock with
        the HiSLIP server."""
        return self.parameter


class AsyncRemoteLocalControl(Message):
    type = MessageType.AsyncRemoteLocalControl


class AsyncRemoteLocalResponse(Message):
    type = MessageType.AsyncRemoteLocalResponse


class AsyncDeviceClear(Message):
    type = MessageType.AsyncDeviceClear


class AsyncDeviceClearAcknowledge(Message):
    type = MessageType.AsyncDeviceClearAcknowledge

    @property
    def feature_bitmap(self):
        """:class:`int`: The feature bitmap that the server prefers."""
        return self.control_code


class DeviceClearComplete(Message):
    type = MessageType.DeviceClearComplete


class DeviceClearAcknowledge(Message):
    type = MessageType.DeviceClearAcknowledge


class Trigger(Message):
    type = MessageType.Trigger


class AsyncMaximumMessageSize(Message):
    type = MessageType.AsyncMaximumMessageSize


class AsyncMaximumMessageSizeResponse(Message):
    type = MessageType.AsyncMaximumMessageSizeResponse

    @property
    def maximum_message_size(self):
        """:class:`int`: The maximum message size that the server's synchronous
        channel accepts."""
        return unpack('!Q', self.payload)[0]


class GetDescriptors(Message):
    type = MessageType.GetDescriptors


class GetDescriptorsResponse(Message):
    type = MessageType.GetDescriptorsResponse


class AsyncInitialize(Message):
    type = MessageType.AsyncInitialize


class AsyncInitializeResponse(Message):
    type = MessageType.AsyncInitializeResponse

    # Flags from Table 3, Section 2.4: Summary of HiSLIP Messages
    SECURE_CONNECTION_SUPPORTED = 1 << 0

    @property
    def secure_connection_supported(self):
        """:class:`bool`: Whether secure connection capability is supported."""
        return bool(self.control_code & self.SECURE_CONNECTION_SUPPORTED)

    @property
    def server_vendor_id(self):
        """:class:`bytes`: The two-character vendor abbreviation of the server."""
        return pack('!H', self.parameter)


class AsyncStatusQuery(Message):
    type = MessageType.AsyncStatusQuery


class AsyncStatusResponse(Message):
    type = MessageType.AsyncStatusResponse

    @property
    def status(self):
        """:class:`int`: The status value."""
        return self.control_code


class StartTLS(Message):
    type = MessageType.StartTLS


class AsyncStartTLS(Message):
    type = MessageType.AsyncStartTLS


class AsyncStartTLSResponse(Message):
    type = MessageType.AsyncStartTLSResponse

    @property
    def busy(self):
        """:class:`bool`: Whether the server is busy."""
        return self.control_code == 0

    @property
    def success(self):
        """:class:`bool`: Whether the request was successful."""
        return self.control_code == 1

    @property
    def error(self):
        """:class:`bool`: Whether there was an error processing the request."""
        return self.control_code == 3


class EndTLS(Message):
    type = MessageType.EndTLS


class AsyncEndTLS(Message):
    type = MessageType.AsyncEndTLS


class AsyncEndTLSResponse(Message):
    type = MessageType.AsyncEndTLSResponse

    @property
    def busy(self):
        """:class:`bool`: Whether the server is busy."""
        return self.control_code == 0

    @property
    def success(self):
        """:class:`bool`: Whether the request was successful."""
        return self.control_code == 1

    @property
    def error(self):
        """:class:`bool`: Whether there was an error processing the request."""
        return self.control_code == 3


class GetSaslMechanismList(Message):
    type = MessageType.GetSaslMechanismList


class GetSaslMechanismListResponse(Message):
    type = MessageType.GetSaslMechanismListResponse

    @property
    def data(self):
        """:class:`list`: List of SASL mechanisms."""
        return self.payload.split()


class AuthenticationStart(Message):
    type = MessageType.AuthenticationStart


class AuthenticationExchange(Message):
    type = MessageType.AuthenticationExchange


class AuthenticationResult(Message):
    type = MessageType.AuthenticationResult

    # Flags in Table 3, Section 2.4: Summary of HiSLIP Messages
    _FAILED = 1 << 0
    _SUCCESS = 1 << 1

    @property
    def data(self):
        """:class:`bytes`: Additional data returned by the server."""
        return self.payload

    @property
    def error(self):
        """:class:`bool`: Whether there was an error processing the request."""
        return self.control_code & self._FAILED

    @property
    def error_code(self):
        """:class:`int`: If authentication fails, the mechanism-dependent error code."""
        return self.parameter

    @property
    def success(self):
        """:class:`bool`: Whether the request was successful."""
        return self.control_code & self._SUCCESS


class HiSLIPClient(object):

    def __init__(self, host):
        """Base class for a HiSLIP client.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(HiSLIPClient, self).__init__()
        self._host = host
        self._socket = None

        # initialize to the default VI_ATTR_TCPIP_HISLIP_MAX_MESSAGE_KB
        self._maximum_server_message_size = 1024 * 1024  # 1 MB

    def close(self):
        """Close the TCP socket, if one is open."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def connect(self, port=PORT, timeout=10):
        """Connect to a specific port of the device.

        Parameters
        ----------
        port : :class:`int`
            The port number to connect to.
        timeout : :class:`float` or :data:`None`, optional
            The maximum number of seconds to wait for the connection to be
            established.
        """
        self.close()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((self._host, port))

    def get_descriptors(self):
        """Descriptors were added in HiSLIP version 2.0 to provide extra
        information about specific server capabilities.

        Returns
        -------
        :class:`GetDescriptorsResponse`
            The response.
        """
        self.write(GetDescriptors())
        return self.read(GetDescriptorsResponse())

    @property
    def maximum_server_message_size(self):
        """:class:`int`: The maximum message size that the server accepts."""
        return self._maximum_server_message_size

    @maximum_server_message_size.setter
    def maximum_server_message_size(self, size):
        self._maximum_server_message_size = int(size)

    def read(self, message, chunk_size=4096):
        """Read a message from the server.

        Parameters
        ----------
        message : :class:`Message`
            An instance of the type of message to read.
        chunk_size : :class:`int`, optional
            The maximum number of bytes to receive at a time.

        Returns
        -------
        :class:`Message`
            The `message` that was passed in, but with its attributes updated
            with the information from the received data.
        """
        header_size = message.header.size
        data = self._socket.recv(header_size)
        if len(data) != header_size:
            reason = 'The reply header is != {} bytes'.format(header_size)
            raise FatalError(ErrorType.BAD_HEADER, reason=reason)

        prologue, typ, code, param, length = message.header.unpack_from(data)

        if prologue != b'HS':
            raise FatalError(ErrorType.BAD_HEADER, reason='prologue != HS')

        size = 0
        payload = bytearray(length)  # preallocate
        view = memoryview(payload)  # avoids unnecessarily copying of slices
        recv_into = self._socket.recv_into
        while size < length:
            request_size = min(chunk_size, length - size)
            received_size = recv_into(view, request_size)
            view = view[received_size:]
            size += received_size
        message.payload = payload

        if typ == MessageType.FatalError:
            raise FatalError(code, reason=payload.decode('ascii'))

        if typ == MessageType.Error:
            raise Error(code, reason=payload.decode('ascii'))

        if message.type is None:
            try:
                message.type = MessageType(typ)
            except ValueError as e:
                raise Error(ErrorType.BAD_MESSAGE_TYPE, reason=str(e))
        elif message.type != typ:
            reason = 'Expected {!r}, received {!r}'.format(message.type, typ)
            raise Error(ErrorType.BAD_MESSAGE_TYPE, reason=reason)

        message.control_code = code
        message.parameter = param
        return message

    def get_timeout(self):
        """Get the socket timeout value.

        Returns
        -------
        :class:`float` or :data:`None`
            The timeout, in seconds, of the socket.
        """
        return self._socket.gettimeout()

    def set_timeout(self, timeout):
        """Set the socket timeout value.

        Parameters
        ----------
        timeout : :class:`float` or :data:`None`
            The timeout, in seconds, to use for the socket.
        """
        self._socket.settimeout(timeout)

    @property
    def socket(self):
        """:class:`~socket.socket`: The reference to the socket."""
        return self._socket

    def write(self, message):
        """Write a message to the server.

        Parameters
        ----------
        message : :class:`Message`
            The message to write.
        """
        if message.size > self._maximum_server_message_size:
            reason = '{} > {}'.format(message.size, self._maximum_server_message_size)
            raise Error(ErrorType.MESSAGE_TOO_LARGE, reason=reason)
        self._socket.sendall(message.pack())


class SyncClient(HiSLIPClient):

    def __init__(self, host):
        """A synchronous connection to the HiSLIP server.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(SyncClient, self).__init__(host)
        self._rmt = 0
        self._message_id = 0xFFFFFF00
        self._previous_message_id = self._message_id - 2
        self._message_id_received = self._message_id - 2
        self._sending_blocked = False

    def device_clear_complete(self, feature_bitmap):
        """Send the device-clear complete message.

        Also resets the message id.

        Parameters
        ----------
        feature_bitmap : :class:`int`
            The feature bitmap of the server
            (i.e., :attr:`AsyncDeviceClearAcknowledge.feature_bitmap`).

        Returns
        -------
        :class:`DeviceClearAcknowledge`
            The response.
        """
        self.write(DeviceClearComplete(feature_bitmap))
        msg = self.read(DeviceClearAcknowledge())

        # Step 8, Section 6.12: Device Clear Transaction
        # The MesssageID is reset to 0xffff ff00
        self._message_id = 0xFFFFFF00
        self._previous_message_id = self._message_id - 2
        self._message_id_received = self._message_id - 2
        return msg

    def _increment_message_id(self):
        """Must be called after the client sends a `Data`, `DataEND` or
        `Trigger` message."""
        self._rmt = 0
        self._previous_message_id = self._message_id

        # Section 3.1.2: Synchronized Mode Client Requirements
        # increment by 2 and wrap to 0 on 32-bit overflow
        self._message_id = (self._message_id + 2) & 0xFFFFFFFF

    def initialize(self, major=1, minor=0, client_id=b'XX', sub_address=b''):
        """Initialize the synchronous connection.

        Parameters
        ----------
        major : :class:`int`, optional
            The major version number of the HiSLIP protocol that the client
            supports.
        minor : :class:`int`, optional
            The minor version number of the HiSLIP protocol that the client
            supports.
        client_id : :class:`bytes`, optional
            The vendor ID of the client. Must have a length of 2 characters.
        sub_address : :class:`bytes`, optional
            A particular device managed by this server. For VISA clients this
            field corresponds to the VISA LAN device name (default is `hislip0`).
            The maximum length is 256 characters.

        Returns
        -------
        :class:`InitializeResponse`
            The response.
        """
        if len(client_id) != 2:
            raise ValueError("The 'client_id' must be 2 characters")

        if len(sub_address) > 256:
            raise ValueError("Maximum length for 'sub_address' is 256 characters")

        # Section 3.1.2: Synchronized Mode Client Requirements
        # The MesssageID is reset to 0xffff ff00 when the connection is initialized
        self._message_id = 0xFFFFFF00
        self._previous_message_id = self._message_id - 2
        self._message_id_received = self._message_id - 2

        self.write(Initialize(major, minor, client_id, sub_address))
        return self.read(InitializeResponse())

    @property
    def message_id(self):
        """:class:`int`: The id of the most-recent message that has completed."""
        return self._previous_message_id

    @property
    def message_id_received(self):
        """:class:`int`: The id of most-recent message that has been received from the server."""
        return self._message_id_received

    def receive(self, size=None, max_size=None, chunk_size=4096):
        """Receive data.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read. If not specified, then read until a
            Response Message Terminator (RMT) is detected.
        max_size : :class:`int`, optional
            The maximum number of bytes that can be read. If not specified,
            then there is no limit.
        chunk_size : :class:`int`, optional
            The maximum number of bytes to receive at a time.

        Returns
        -------
        :class:`bytearray`
            The received data.
        """
        timeout = self.get_timeout()
        try:
            # _receive() decreases the timeout after each Message is read
            return self._receive(timeout, size, max_size, chunk_size)
        finally:
            # make sure the socket timeout goes back to what it was originally
            self.set_timeout(timeout)

    def _receive(self, timeout, size, max_size, chunk_size):
        async_interrupted_received = False
        interrupted_received = False
        discard_data = False
        not_done = True
        data = bytearray()
        t0 = time.time()
        while not_done:
            msg = self.read(Message(), chunk_size=chunk_size)

            # These 'if' statements follow the guidelines in
            # Section 3.1.2: Synchronized Mode Client Requirements
            if msg.type == MessageType.DataEnd:
                # 4. If the client initially detects AsyncInterrupted, it shall
                # also discard any further Data or DataEND messages from the
                # server until Interrupted is encountered.
                if discard_data:
                    continue

                # Section 6.15: Establish Secure Connection Transaction
                self._message_id_received = msg.parameter

                # 1. When receiving DataEND (that is an RMT), verify that the
                # MessageID indicated in the DataEND message is the MessageID
                # that the client sent to the server with the most recent Data,
                # DataEND or Trigger message. If the MessageIDs do not match,
                # the client shall clear any Data responses already buffered
                # and discard the offending DataEND message.
                if msg.parameter != self._previous_message_id:
                    # TODO Python 2 does not have the bytearray.clear() method.
                    #  Use it for each 'elif' case when dropping v2 support.
                    data = bytearray()
                    continue

                self._rmt = 1  # msg contains the Response Message Terminator (RMT)
                not_done = False

            elif msg.type == MessageType.Data:
                # 4. If the client initially detects AsyncInterrupted, it shall
                # also discard any further Data or DataEND messages from the
                # server until Interrupted is encountered.
                if discard_data:
                    continue

                # Section 6.15: Establish Secure Connection Transaction
                self._message_id_received = msg.parameter

                # 2. When receiving Data messages if the MessageID is not
                # 0xffffffff, then verify that the MessageID indicated in the
                # Data message is the MessageID that the client sent to the
                # server with the most recent Data, DataEND or Trigger message.
                # If the MessageIDs do not match, the client shall clear any
                # Data responses already buffered and discard the offending
                # Data message.
                if msg.parameter != 0xFFFFFFFF and \
                        (msg.parameter != self._previous_message_id):
                    data = bytearray()
                    continue

            elif msg.type == MessageType.AsyncInterrupted:
                async_interrupted_received = True

                # 4. When the client receives Interrupted or AsyncInterrupted,
                # it shall clear any whole or partial server messages that have
                # been validated per rules 1 and 2.
                data = bytearray()

                # 4. If the client initially detects AsyncInterrupted, it shall
                # also discard any further Data or DataEND messages from the
                # server until Interrupted is encountered.
                if not interrupted_received:
                    discard_data = True

                # 4. If the client detects Interrupted before it detects
                # AsyncInterrupted, the client shall not send any further
                # messages until AsyncInterrupted is received.
                self._sending_blocked = False

                continue

            elif msg.type == MessageType.Interrupted:
                interrupted_received = True

                # 4. When the client receives Interrupted or AsyncInterrupted, it
                # shall clear any whole or partial server messages that have been
                # validated per rules 1 and 2.
                data = bytearray()

                # 4. If the client initially detects AsyncInterrupted, it shall
                # also discard any further Data or DataEND messages from the
                # server until Interrupted is encountered.
                discard_data = False

                # 4. If the client detects Interrupted before it detects
                # AsyncInterrupted, the client shall not send any further
                # messages until AsyncInterrupted is received.
                if not async_interrupted_received:
                    self._sending_blocked = True

                continue

            else:  # ignore all other message types
                continue

            data.extend(msg.payload)

            if size is not None and len(data) > size:
                return data[:size]

            if max_size is not None and len(data) > max_size:
                reason = 'len(message) [{}] > max_read_size [{}]'.format(
                    len(data), max_size)
                raise FatalError(0, reason=reason)

            if not_done and timeout is not None:
                elapsed_time = time.time() - t0
                if elapsed_time > timeout:
                    reason = 'timeout after {} seconds'.format(timeout)
                    raise FatalError(0, reason=reason)

                # decrease the timeout when reading each Message so that the
                # total time to receive all Messages preserves what was specified
                self.set_timeout(max(0, timeout - elapsed_time))

        return data

    @property
    def rmt(self):
        """:class:`int` The current state of the Response Message Terminator (RMT)."""
        return self._rmt

    def send(self, data):
        """Send data with the Response Message Terminator (RMT) character.

        Parameters
        ----------
        data : :class:`bytes`
            The data to send.

        Returns
        -------
        :class:`int`
            The number of bytes sent.
        """
        if self._sending_blocked:
            # Section 3.1.2: Synchronized Mode Client Requirements
            # 4. If the client detects Interrupted before it detects
            # AsyncInterrupted, the client shall not send any further
            # messages until AsyncInterrupted is received.
            raise RuntimeError('Cannot send data, '
                               'must wait for an AsyncInterrupted message')

        view = memoryview(data)  # avoids unnecessarily copying of slices
        max_size = self._maximum_server_message_size - Message.header.size
        remaining = len(data)
        while remaining > 0:
            if remaining > max_size:
                self.write(Data(self._rmt, self._message_id, view[:max_size]))
                sent = max_size
            else:
                self.write(DataEnd(self._rmt, self._message_id, view))
                sent = remaining
            view = view[sent:]
            remaining -= sent
            self._increment_message_id()
        return len(data)

    def trigger(self):
        """Send the trigger message (emulates a GPIB Group Execute Trigger event)."""
        self.write(Trigger(self._rmt, self._message_id))
        self._increment_message_id()

    def start_tls(self):
        """Send the `StartTLS` message."""
        self.write(StartTLS())

    def end_tls(self):
        """Send the `EndTLS` message."""
        self.write(EndTLS())

    def get_sasl_mechanism_list(self):
        """Request the list of SASL mechanisms from the server.

        Returns
        -------
        :class:`GetSaslMechanismListResponse`
            The response.
        """
        self.write(GetSaslMechanismList())
        return self.read(GetSaslMechanismListResponse())

    def authentication_start(self, mechanism):
        """Send a SASL authentication method to the server.

        Parameters
        ----------
        mechanism : :class:`bytes`
            The selected mechanism to use for authentication.
        """
        self.write(AuthenticationStart(payload=mechanism))

    def write_authentication_exchange(self, data):
        """Send exchange data during the authentication transaction.

        Parameters
        ----------
        data : :class:`bytes`
            The data to send.
        """
        self.write(AuthenticationExchange(payload=data))

    def read_authentication_exchange(self):
        """Receive exchange data during the authentication transaction.

        Returns
        -------
        :class:`AuthenticationExchange`
            The exchange.
        """
        return self.read(AuthenticationExchange())

    def authentication_result(self):
        """Receive an authentication result from the server.

        Returns
        -------
        :class:`AuthenticationResult`
            The result.
        """
        return self.read(AuthenticationResult())


class AsyncClient(HiSLIPClient):

    def __init__(self, host):
        """An asynchronous connection to the HiSLIP server.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(AsyncClient, self).__init__(host)

    def async_initialize(self, session_id):
        """Initialize the asynchronous connection.

        Parameters
        ----------
        session_id : :class:`int`
            The session ID.

        Returns
        -------
        :class:`AsyncInitializeResponse`
            The response.
        """
        self.write(AsyncInitialize(parameter=session_id))
        return self.read(AsyncInitializeResponse())

    def async_maximum_message_size(self, size):
        """Exchange the maximum message sizes that are accepted between the
        client and server.

        Parameters
        ----------
        size : :class:`int`
            The maximum message size that the client accepts.

        Returns
        -------
        :class:`AsyncMaximumMessageSizeResponse`
            The maximum message size that the server accepts.
        """
        self.write(AsyncMaximumMessageSize(payload=pack('!Q', size)))
        msg = AsyncMaximumMessageSizeResponse()
        self.read(msg)
        self.maximum_server_message_size = msg.maximum_message_size
        return msg

    def async_lock_request(self, timeout=None, lock_string=''):
        """Request a lock.

        Parameters
        ----------
        timeout : :class:`float`, optional
            The number of seconds to wait to acquire a lock. A timeout of 0
            indicates that the HiSLIP server should only grant the lock if
            it is available immediately.
        lock_string : :class:`str`, optional
            An ASCII string that identifies this lock. If not specified, then
            an exclusive lock is requested, otherwise the string indicates an
            identification of a shared-lock request. The maximum length is
            256 characters.

        Returns
        -------
        :class:`AsyncLockResponse`
            The response.
        """
        if len(lock_string) > 256:
            raise ValueError('len(lock_string) > 256')

        socket_timeout = self.get_timeout()
        if timeout is None:
            timeout = 86400  # consider 1 day as "wait forever"
        self.set_timeout(10 + timeout)  # socket timeout must be larger
        timeout_ms = int(timeout * 1000)
        try:
            self.write(AsyncLock(1, timeout_ms, lock_string.encode('ascii')))
            return self.read(AsyncLockResponse())
        finally:
            self.set_timeout(socket_timeout)

    def async_lock_release(self, message_id):
        """Release a lock.

        Parameters
        ----------
        message_id : :class:`int`
            The most recent message id that was completed on the synchronous
            channel (i.e., :attr:`SyncClient.message_id`).

        Returns
        -------
        :class:`AsyncLockResponse`
            The response.
        """
        self.write(AsyncLock(0, message_id))
        return self.read(AsyncLockResponse())

    def async_lock_info(self):
        """Request the lock status from the HiSLIP server.

        Returns
        -------
        :class:`AsyncLockInfoResponse`
            The response.
        """
        self.write(AsyncLockInfo())
        return self.read(AsyncLockInfoResponse())

    def async_remote_local_control(self, request, message_id):
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

        message_id : :class:`int`
            The most recent message id that was completed on the synchronous
            channel (i.e., :attr:`SyncClient.message_id`).

        Returns
        -------
        :class:`AsyncRemoteLocalResponse`
            The response.
        """
        self.write(AsyncRemoteLocalControl(request, message_id))
        return self.read(AsyncRemoteLocalResponse())

    def async_device_clear(self):
        """Send the device clear request.

        Returns
        -------
        :class:`AsyncDeviceClearAcknowledge`
            The response.
        """
        self.write(AsyncDeviceClear())
        return self.read(AsyncDeviceClearAcknowledge())

    def async_status_query(self, synchronous):
        """Status query transaction.

        The status query provides an 8-bit status response from the server that
        corresponds to the VISA `viReadSTB` operation.

        Parameters
        ----------
        synchronous : :class:`SyncClient`
            The synchronous client that corresponds with this asynchronous client.

        Returns
        -------
        :class:`AsyncStatusResponse`
            The response.
        """
        if not isinstance(synchronous, SyncClient):
            raise TypeError('Must pass in a synchronous-client object')
        self.write(AsyncStatusQuery(synchronous.rmt, synchronous.message_id))
        return self.read(AsyncStatusResponse())

    def async_start_tls(self, synchronous):
        """Initiate the secure connection transaction.

        Parameters
        ----------
        synchronous : :class:`SyncClient`
            The synchronous client that corresponds with this asynchronous client.

        Returns
        -------
        :class:`AsyncStartTLSResponse`
            The response.
        """
        if not isinstance(synchronous, SyncClient):
            raise TypeError('Must pass in a synchronous-client object')

        payload = pack('!I', synchronous.message_id_received)
        self.write(AsyncStartTLS(synchronous.rmt, synchronous.message_id, payload))
        return self.read(AsyncStartTLSResponse())

    def async_end_tls(self, synchronous):
        """Initiate the end of the secure connection transaction.

        Parameters
        ----------
        synchronous : :class:`SyncClient`
            The synchronous client that corresponds with this asynchronous client.

        Returns
        -------
        :class:`AsyncEndTLSResponse`
            The response.
        """
        if not isinstance(synchronous, SyncClient):
            raise TypeError('Must pass in a synchronous-client object')

        payload = pack('!I', synchronous.message_id_received)
        self.write(AsyncEndTLS(synchronous.rmt, synchronous.message_id, payload))
        return self.read(AsyncEndTLSResponse())
