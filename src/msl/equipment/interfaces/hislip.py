"""Implementation of the [HiSLIP] protocol for a client.

This module implements the following IVI Protocol Specification:

`IVI-6.1: High-Speed LAN Instrument Protocol (HiSLIP) v2.0 April 23, 2020`

[HiSLIP]: https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf
"""

from __future__ import annotations

import re
import socket
import time
from dataclasses import dataclass
from enum import IntEnum
from struct import Struct, pack, unpack
from typing import TYPE_CHECKING

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from typing import Any, ClassVar, TypeVar

    from msl.equipment.schema import Equipment

    T = TypeVar("T", bound="Message")


REGEX = re.compile(
    r"TCPIP(?P<board>\d*)::(?P<host>[^\s:]+)::(?P<name>(hislip\d+))(,(?P<port>\d+))?(::INSTR)?$", flags=re.IGNORECASE
)

PORT = 4880
ONE_DAY = 86400.0  # use 1 day as equivalent to waiting forever for a lock


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

    # Just a placeholder to be updated by an appropriate type in a Message subclass
    UNDEFINED = 9999


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


class HiSLIPError(OSError):
    """Base class for all HiSLIP exceptions."""

    _mapping: ClassVar[dict[int, bytes]] = {}  # each subclass must override

    def __init__(self, message_type: MessageType, control_code: int, reason: str = "") -> None:
        """Base class for HiSLIP exceptions.

        Args:
            message_type: The message type.
            control_code: The control code from the server response.
            reason: Additional information to display in exception string.
        """
        super().__init__()
        if control_code not in self._mapping:
            control_code = ErrorType.UNIDENTIFIED
        self.reason: str | None = reason
        self._message: Message = Message()
        self._message.type = message_type
        self._message.control_code = control_code
        self._message.payload = self._mapping[control_code]

    @property
    def message(self) -> Message:
        """The error message that can be written to the server."""
        return self._message

    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation of the error."""
        code = self._message.control_code
        text = bytes(self._message.payload).decode()
        if self.reason:
            return f"{text} [code={code}, reason={self.reason!r}]"
        return f"{text} [code={code}]"


# Table 14, Section 6.2: Fatal Error Detection and Synchronization Recovery
class FatalError(HiSLIPError):
    """Exception for a fatal error."""

    _mapping: ClassVar[dict[int, bytes]] = {
        ErrorType.UNIDENTIFIED: b"Unidentified error",
        ErrorType.BAD_HEADER: b"Poorly formed message header",
        ErrorType.CHANNELS_INACTIVATED: b"Attempt to use connection without both channels established",
        ErrorType.INVALID_INIT_SEQUENCE: b"Invalid initialization sequence",
        ErrorType.MAX_CLIENTS: b"Server refused connection due to maximum number of clients exceeded",
    }

    def __init__(self, control_code: int, reason: str = "") -> None:
        """Exception for a fatal error.

        Args:
            control_code: The control code from the server response.
            reason: Additional information to display in exception string.
        """
        super().__init__(MessageType.FatalError, control_code, reason)


# Table 16, Section 6.3: Error Notification Transaction
class Error(HiSLIPError):
    """Exception for a non-fatal error."""

    _mapping: ClassVar[dict[int, bytes]] = {
        ErrorType.UNIDENTIFIED: b"Unidentified error",
        ErrorType.BAD_MESSAGE_TYPE: b"Unrecognized message type",
        ErrorType.BAD_CONTROL_CODE: b"Unrecognized control code",
        ErrorType.BAD_VENDOR: b"Unrecognized vendor defined message",
        ErrorType.MESSAGE_TOO_LARGE: b"Message too large",
        ErrorType.AUTHENTICATION_FAILED: b"Authentication failed",
    }

    def __init__(self, control_code: int, reason: str = "") -> None:
        """Exception for a non-fatal error.

        Args:
            control_code: The control code from the server response.
            reason: Additional information to display in exception string.
        """
        super().__init__(MessageType.Error, control_code, reason)


class Message:
    """A HiSLIP message."""

    header: Struct = Struct("!2s2BIQ")
    prologue: bytes = b"HS"
    type: MessageType = MessageType.UNDEFINED

    def __init__(
        self, control_code: int = 0, parameter: int = 0, payload: bytes | bytearray | memoryview = b""
    ) -> None:
        """Create a new HiSLIP message.

        Args:
            control_code: This 8-bit field is a general parameter for the message.
            parameter: This 32-bit field has various uses in different messages.
            payload: The payload data.
        """
        self.control_code: int = control_code
        self.parameter: int = parameter
        self.payload: bytes | bytearray | memoryview = payload

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        if not self.payload:
            payload = "payload=b''"
        elif len(self.payload) < 50:  # noqa: PLR2004
            payload = f"payload={self.payload!r}"
        else:
            payload = f"payload[len={self.length_payload}]={self.payload[:25]!r}...{self.payload[-25:]!r}"

        name = self.type.name
        return f"Message(type={name}, control_code={self.control_code}, parameter={self.parameter}, {payload})"

    @property
    def length_payload(self) -> int:
        """The length of the payload."""
        return len(self.payload)

    def pack(self) -> bytearray:
        """Convert the message to bytes.

        Returns:
            The messaged packed as bytes.
        """
        data = bytearray(
            self.header.pack(self.prologue, self.type, self.control_code, self.parameter, self.length_payload)
        )
        data.extend(self.payload)
        return data

    @staticmethod
    def repack(unpack_fmt: str, pack_fmt: str, *args: Any) -> tuple[Any, ...]:  # noqa: ANN401
        """Convert arguments from one byte format to another.

        Args:
            unpack_fmt: The format to convert the arguments to.
            pack_fmt: The format that the arguments are currently in.
            *args: The arguments to convert.

        Returns:
            The converted arguments.
        """
        return unpack(unpack_fmt, pack(pack_fmt, *args))

    @property
    def size(self) -> int:
        """The total size of the message."""
        return self.header.size + self.length_payload


class FatalErrorMessage(Message):
    """FatalErrorMessage message."""

    type: MessageType = MessageType.FatalError


class ErrorMessage(Message):
    """ErrorMessage message."""

    type: MessageType = MessageType.Error


class Initialize(Message):
    """Initialize message."""

    type: MessageType = MessageType.Initialize

    def __init__(self, major: int, minor: int, client_id: bytes, sub_address: bytes) -> None:
        """Create an Initialize message.

        Args:
            major: The major version number of the HiSLIP protocol that the client supports.
            minor: The minor version number of the HiSLIP protocol that the client supports.
            client_id: The vendor ID of the client. Must have a length of 2 characters.
            sub_address: A particular device managed by this server. For VISA clients this
                field corresponds to the VISA LAN device name (default is `hislip0`).
                The maximum length is 256 characters.
        """
        super().__init__(payload=sub_address)
        self.parameter: int
        (self.parameter,) = self.repack("!I", "!2B2s", major, minor, client_id)


class InitializeResponse(Message):
    """InitializeResponse message."""

    type: MessageType = MessageType.InitializeResponse

    # Flags from Table 12 (Step 3), Section 6.1: Initialization Transaction
    _OVERLAP_MODE: int = 1 << 0
    _ENCRYPTION_MODE: int = 1 << 1
    _INITIAL_ENCRYPTION: int = 1 << 2

    @property
    def encrypted(self) -> bool:
        """Whether encryption is optional or mandatory."""
        return bool(self.control_code & self._ENCRYPTION_MODE)

    @property
    def initial_encryption(self) -> bool:
        """Whether the client shall switch to encrypted mode."""
        return bool(self.control_code & self._INITIAL_ENCRYPTION)

    @property
    def overlapped(self) -> bool:
        """Whether the server is in overlapped or synchronous mode."""
        return bool(self.control_code & self._OVERLAP_MODE)

    @property
    def protocol_version(self) -> tuple[int, int]:
        """The (major, minor) version numbers of the HiSLIP protocol that the client and server are to use."""
        return self.repack("!2BH", "!I", self.parameter)[:2]

    @property
    def session_id(self) -> int:
        """The session ID."""
        _id: int = self.repack("!2BH", "!I", self.parameter)[2]
        return _id


class Data(Message):
    """Data message."""

    type: MessageType = MessageType.Data


class DataEnd(Message):
    """DataEnd message."""

    type: MessageType = MessageType.DataEnd


class AsyncLock(Message):
    """AsyncLock message."""

    type: MessageType = MessageType.AsyncLock


class AsyncLockResponse(Message):
    """AsyncLockResponse message."""

    type: MessageType = MessageType.AsyncLockResponse

    # Table 19 and 20, Section 6.5: Lock Transaction
    _FAILURE: int = 0
    _SUCCESS: int = 1
    _SHARED: int = 2
    _ERROR: int = 3

    @property
    def error(self) -> bool:
        """Whether the request was an invalid attempt to release a lock that was not acquired or to request a lock already granted."""  # noqa: E501
        return self.control_code == self._ERROR

    @property
    def failed(self) -> bool:
        """Whether a lock was requested but not granted (timeout expired)."""
        return self.control_code == self._FAILURE

    @property
    def success(self) -> bool:
        """Whether requesting or releasing the lock was successful."""
        return self.control_code in (self._SUCCESS, self._SHARED)

    @property
    def shared_released(self) -> bool:
        """Whether releasing a shared lock was successful."""
        return self.control_code == self._SHARED


class AsyncLockInfo(Message):
    """AsyncLockInfo message."""

    type: MessageType = MessageType.AsyncLockInfo


class AsyncLockInfoResponse(Message):
    """AsyncLockInfoResponse message."""

    type: MessageType = MessageType.AsyncLockInfoResponse

    @property
    def exclusive(self) -> bool:
        """Whether the HiSLIP server has an exclusive lock with a client."""
        return self.control_code == 1

    @property
    def num_locks(self) -> int:
        """The number of HiSLIP clients that have a lock with the HiSLIP server."""
        return self.parameter


class AsyncRemoteLocalControl(Message):
    """AsyncRemoteLocalControl message."""

    type: MessageType = MessageType.AsyncRemoteLocalControl


class AsyncRemoteLocalResponse(Message):
    """AsyncRemoteLocalResponse message."""

    type: MessageType = MessageType.AsyncRemoteLocalResponse


class AsyncDeviceClear(Message):
    """AsyncDeviceClear message."""

    type: MessageType = MessageType.AsyncDeviceClear


class AsyncDeviceClearAcknowledge(Message):
    """AsyncDeviceClearAcknowledge message."""

    type: MessageType = MessageType.AsyncDeviceClearAcknowledge

    @property
    def feature_bitmap(self) -> int:
        """The feature bitmap that the server prefers."""
        return self.control_code


class DeviceClearComplete(Message):
    """DeviceClearComplete message."""

    type: MessageType = MessageType.DeviceClearComplete


class DeviceClearAcknowledge(Message):
    """DeviceClearAcknowledge message."""

    type: MessageType = MessageType.DeviceClearAcknowledge


class Trigger(Message):
    """Trigger message."""

    type: MessageType = MessageType.Trigger


class AsyncMaximumMessageSize(Message):
    """AsyncMaximumMessageSize message."""

    type: MessageType = MessageType.AsyncMaximumMessageSize


class AsyncMaximumMessageSizeResponse(Message):
    """AsyncMaximumMessageSizeResponse message."""

    type: MessageType = MessageType.AsyncMaximumMessageSizeResponse

    @property
    def maximum_message_size(self) -> int:
        """The maximum message size that the server's synchronous channel accepts."""
        size: int = unpack("!Q", self.payload)[0]
        return size


class GetDescriptors(Message):
    """GetDescriptors message."""

    type: MessageType = MessageType.GetDescriptors


class GetDescriptorsResponse(Message):
    """GetDescriptorsResponse message."""

    type: MessageType = MessageType.GetDescriptorsResponse


class AsyncInitialize(Message):
    """AsyncInitialize message."""

    type: MessageType = MessageType.AsyncInitialize


class AsyncInitializeResponse(Message):
    """AsyncInitializeResponse message."""

    type: MessageType = MessageType.AsyncInitializeResponse

    # Flags from Table 3, Section 2.4: Summary of HiSLIP Messages
    SECURE_CONNECTION_SUPPORTED: int = 1 << 0

    @property
    def secure_connection_supported(self) -> bool:
        """Whether secure connection capability is supported."""
        return bool(self.control_code & self.SECURE_CONNECTION_SUPPORTED)

    @property
    def server_vendor_id(self) -> bytes:
        """The two-character vendor abbreviation of the server."""
        return pack("!H", self.parameter)


class AsyncStatusQuery(Message):
    """AsyncStatusQuery message."""

    type: MessageType = MessageType.AsyncStatusQuery


class AsyncStatusResponse(Message):
    """AsyncStatusResponse message."""

    type: MessageType = MessageType.AsyncStatusResponse

    @property
    def status(self) -> int:
        """The status value."""
        return self.control_code


class StartTLS(Message):
    """StartTLS message."""

    type: MessageType = MessageType.StartTLS


class AsyncStartTLS(Message):
    """AsyncStartTLS message."""

    type: MessageType = MessageType.AsyncStartTLS


class AsyncStartTLSResponse(Message):
    """AsyncStartTLSResponse message."""

    type: MessageType = MessageType.AsyncStartTLSResponse

    @property
    def busy(self) -> bool:
        """Whether the server is busy."""
        return self.control_code == 0

    @property
    def success(self) -> bool:
        """Whether the request was successful."""
        return self.control_code == 1

    @property
    def error(self) -> bool:
        """Whether there was an error processing the request."""
        return self.control_code == 3  # noqa: PLR2004


class EndTLS(Message):
    """EndTLS message."""

    type: MessageType = MessageType.EndTLS


class AsyncEndTLS(Message):
    """AsyncEndTLS message."""

    type: MessageType = MessageType.AsyncEndTLS


class AsyncEndTLSResponse(Message):
    """AsyncEndTLSResponse message."""

    type: MessageType = MessageType.AsyncEndTLSResponse

    @property
    def busy(self) -> bool:
        """Whether the server is busy."""
        return self.control_code == 0

    @property
    def success(self) -> bool:
        """Whether the request was successful."""
        return self.control_code == 1

    @property
    def error(self) -> bool:
        """Whether there was an error processing the request."""
        return self.control_code == 3  # noqa: PLR2004


class GetSaslMechanismList(Message):
    """GetSaslMechanismList message."""

    type: MessageType = MessageType.GetSaslMechanismList


class GetSaslMechanismListResponse(Message):
    """GetSaslMechanismListResponse message."""

    type: MessageType = MessageType.GetSaslMechanismListResponse

    @property
    def data(self) -> list[bytes]:
        """List of SASL mechanisms."""
        return bytes(self.payload).split()


class AuthenticationStart(Message):
    """AuthenticationStart message."""

    type: MessageType = MessageType.AuthenticationStart


class AuthenticationExchange(Message):
    """AuthenticationExchange message."""

    type: MessageType = MessageType.AuthenticationExchange


class AuthenticationResult(Message):
    """AuthenticationResult message."""

    type: MessageType = MessageType.AuthenticationResult

    # Flags in Table 3, Section 2.4: Summary of HiSLIP Messages
    _FAILED: int = 1 << 0
    _SUCCESS: int = 1 << 1

    @property
    def data(self) -> bytes:
        """Additional data returned by the server."""
        return bytes(self.payload)

    @property
    def error(self) -> bool:
        """Whether there was an error processing the request."""
        return bool(self.control_code & self._FAILED)

    @property
    def error_code(self) -> int:
        """If authentication fails, the mechanism-dependent error code."""
        return self.parameter

    @property
    def success(self) -> bool:
        """Whether the request was successful."""
        return bool(self.control_code & self._SUCCESS)


class HiSLIPClient:
    """Base class for a HiSLIP client."""

    def __init__(self, host: str) -> None:
        """Base class for a HiSLIP client.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__()
        self._host: str = host
        self._socket: socket.socket | None = None

        # initialize to the default VI_ATTR_TCPIP_HISLIP_MAX_MESSAGE_KB
        self._maximum_server_message_size: int = 1048576  # 1 MB

    def close(self) -> None:
        """Close the TCP socket, if one is open."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def connect(self, port: int = PORT, timeout: float | None = 10) -> None:
        """Connect to a specific port of the device.

        Args:
            port: The port number to connect to.
            timeout: The maximum number of seconds to wait for the connection to be established.
        """
        self.close()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((self._host, port))

    def get_descriptors(self) -> GetDescriptorsResponse:
        """Descriptors were added in HiSLIP version 2.0 to provide extra information about specific server capabilities.

        Returns:
            The response.
        """
        self.write(GetDescriptors())
        return self.read(GetDescriptorsResponse())

    @property
    def maximum_server_message_size(self) -> int:
        """The maximum message size that the server accepts."""
        return self._maximum_server_message_size

    @maximum_server_message_size.setter
    def maximum_server_message_size(self, size: int) -> None:
        self._maximum_server_message_size = int(size)

    def read(self, message: T, chunk_size: int = 4096) -> T:
        """Read a message from the server.

        Args:
            message: An instance of the type of message to read.
            chunk_size: The maximum number of bytes to receive at a time.

        Returns:
            The `message` that was passed in, but with its attributes updated with the
                information from the received data.
        """
        if self._socket is None:
            raise FatalError(ErrorType.CHANNELS_INACTIVATED, reason="socket closed")

        header_size = message.header.size
        data = self._socket.recv(header_size)
        if len(data) != header_size:
            reason = f"The reply header is != {header_size} bytes"
            raise FatalError(ErrorType.BAD_HEADER, reason=reason)

        prologue, typ, code, param, length = message.header.unpack_from(data)

        if prologue != b"HS":
            raise FatalError(ErrorType.BAD_HEADER, reason="prologue != HS")

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
            raise FatalError(code, reason=payload.decode("ascii"))

        if typ == MessageType.Error:
            raise Error(code, reason=payload.decode("ascii"))

        if message.type == MessageType.UNDEFINED:
            try:
                message.type = MessageType(typ)
            except ValueError as e:
                raise Error(ErrorType.BAD_MESSAGE_TYPE, reason=str(e)) from None
        elif message.type != typ:
            reason = f"Expected {message.type!r}, received {typ!r}"
            raise Error(ErrorType.BAD_MESSAGE_TYPE, reason=reason)

        message.control_code = code
        message.parameter = param
        return message

    def get_timeout(self) -> float | None:
        """Get the socket timeout value.

        Returns:
            The timeout, in seconds, of the socket.
        """
        if self._socket is None:
            return None
        return self._socket.gettimeout()

    def set_timeout(self, timeout: float | None) -> None:
        """Set the socket timeout value.

        Args:
            timeout: The timeout, in seconds, to use for the socket.
        """
        if self._socket is None:
            raise FatalError(ErrorType.CHANNELS_INACTIVATED, reason="socket closed")
        self._socket.settimeout(timeout)

    @property
    def socket(self) -> socket.socket | None:
        """The reference to the socket."""
        return self._socket

    def write(self, message: Message) -> None:
        """Write a message to the server.

        Args:
            message: The message to write.
        """
        if self._socket is None:
            raise FatalError(ErrorType.CHANNELS_INACTIVATED, reason="socket closed")

        if message.size > self._maximum_server_message_size:
            reason = f"{message.size} > {self._maximum_server_message_size}"
            raise Error(ErrorType.MESSAGE_TOO_LARGE, reason=reason)

        self._socket.sendall(message.pack())


class SyncClient(HiSLIPClient):
    """A synchronous connection to the HiSLIP server."""

    def __init__(self, host: str) -> None:
        """A synchronous connection to the HiSLIP server.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)
        self._rmt: int = 0
        self._message_id: int = 0xFFFFFF00
        self._previous_message_id: int = self._message_id - 2
        self._message_id_received: int = self._message_id - 2
        self._sending_blocked: bool = False

    def device_clear_complete(self, feature_bitmap: int) -> DeviceClearAcknowledge:
        """Send the device-clear complete message.

        Also resets the message id.

        Args:
            feature_bitmap: The feature bitmap of the server, i.e., `AsyncDeviceClearAcknowledge.feature_bitmap`.

        Returns:
            The response.
        """
        self.write(DeviceClearComplete(feature_bitmap))
        msg = self.read(DeviceClearAcknowledge())

        # Step 8, Section 6.12: Device Clear Transaction
        # The MessageID is reset to 0xffff ff00
        self._message_id = 0xFFFFFF00
        self._previous_message_id = self._message_id - 2
        self._message_id_received = self._message_id - 2
        return msg

    def _increment_message_id(self) -> None:
        """Must be called after the client sends a `Data`, `DataEND` or `Trigger` message."""
        self._rmt = 0
        self._previous_message_id = self._message_id

        # Section 3.1.2: Synchronized Mode Client Requirements
        # increment by 2 and wrap to 0 on 32-bit overflow
        self._message_id = (self._message_id + 2) & 0xFFFFFFFF

    def initialize(
        self, major: int = 1, minor: int = 0, client_id: bytes = b"XX", sub_address: bytes = b""
    ) -> InitializeResponse:
        """Initialize the synchronous connection.

        Args:
            major: The major version number of the HiSLIP protocol that the client supports.
            minor: The minor version number of the HiSLIP protocol that the client supports.
            client_id: The vendor ID of the client. Must have a length of 2 characters.
            sub_address: A particular device managed by this server. For VISA clients this
                field corresponds to the VISA LAN device name (default is `hislip0`).
                The maximum length is 256 characters.

        Returns:
            The response.
        """
        if len(client_id) != 2:  # noqa: PLR2004
            msg = "The 'client_id' must be 2 characters"
            raise ValueError(msg)

        if len(sub_address) > 256:  # noqa: PLR2004
            msg = "Maximum length for 'sub_address' is 256 characters"
            raise ValueError(msg)

        # Section 3.1.2: Synchronized Mode Client Requirements
        # The MessageID is reset to 0xffff ff00 when the connection is initialized
        self._message_id = 0xFFFFFF00
        self._previous_message_id = self._message_id - 2
        self._message_id_received = self._message_id - 2

        self.write(Initialize(major, minor, client_id, sub_address))
        return self.read(InitializeResponse())

    @property
    def message_id(self) -> int:
        """The id of the most-recent message that has completed."""
        return self._previous_message_id

    @property
    def message_id_received(self) -> int:
        """The id of most-recent message that has been received from the server."""
        return self._message_id_received

    def receive(self, size: int | None = None, max_size: int | None = None, chunk_size: int = 4096) -> bytearray:
        """Receive data.

        Args:
            size: The number of bytes to read. If not specified, then read until a
                Response Message Terminator (RMT) is detected.
            max_size: The maximum number of bytes that can be read. If not specified, then there is no limit.
            chunk_size: The maximum number of bytes to receive at a time.

        Returns:
            The received data.
        """
        timeout = self.get_timeout()
        try:
            # _receive() decreases the timeout after each Message is read
            return self._receive(timeout, size, max_size, chunk_size)
        finally:
            # make sure the socket timeout goes back to what it was originally
            self.set_timeout(timeout)

    def _receive(self, timeout: float | None, size: int | None, max_size: int | None, chunk_size: int) -> bytearray:  # noqa: C901, PLR0912, PLR0915
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
                    data.clear()
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
                if msg.parameter not in (4294967295, self._previous_message_id):
                    data.clear()
                    continue

            elif msg.type == MessageType.AsyncInterrupted:
                async_interrupted_received = True

                # 4. When the client receives Interrupted or AsyncInterrupted,
                # it shall clear any whole or partial server messages that have
                # been validated per rules 1 and 2.
                data.clear()

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
                data.clear()

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
                reason = f"len(message) [{len(data)}] > max_read_size [{max_size}]"
                raise FatalError(0, reason=reason)

            if not_done and timeout is not None:
                elapsed_time = time.time() - t0
                if elapsed_time > timeout:
                    reason = f"timeout after {timeout} seconds"
                    raise FatalError(0, reason=reason)

                # decrease the timeout when reading each Message so that the
                # total time to receive all Messages preserves what was specified
                self.set_timeout(max(0, timeout - elapsed_time))

        return data

    @property
    def rmt(self) -> int:
        """The current state of the Response Message Terminator (RMT)."""
        return self._rmt

    def send(self, data: bytes) -> int:
        """Send data with the Response Message Terminator (RMT) character.

        Args:
            data: The data to send.

        Returns:
            The number of bytes sent.
        """
        if self._sending_blocked:
            # Section 3.1.2: Synchronized Mode Client Requirements
            # 4. If the client detects Interrupted before it detects
            # AsyncInterrupted, the client shall not send any further
            # messages until AsyncInterrupted is received.
            msg = "Cannot send data, must wait for an AsyncInterrupted message"
            raise RuntimeError(msg)

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

    def trigger(self) -> None:
        """Send the trigger message (emulates a GPIB Group Execute Trigger event)."""
        self.write(Trigger(self._rmt, self._message_id))
        self._increment_message_id()

    def start_tls(self) -> None:
        """Send the `StartTLS` message."""
        self.write(StartTLS())

    def end_tls(self) -> None:
        """Send the `EndTLS` message."""
        self.write(EndTLS())

    def get_sasl_mechanism_list(self) -> GetSaslMechanismListResponse:
        """Request the list of SASL mechanisms from the server.

        Returns:
            The response.
        """
        self.write(GetSaslMechanismList())
        return self.read(GetSaslMechanismListResponse())

    def authentication_start(self, mechanism: bytes) -> None:
        """Send a SASL authentication method to the server.

        Args:
            mechanism: The selected mechanism to use for authentication.
        """
        self.write(AuthenticationStart(payload=mechanism))

    def write_authentication_exchange(self, data: bytes) -> None:
        """Send exchange data during the authentication transaction.

        Args:
            data: The data to send.
        """
        self.write(AuthenticationExchange(payload=data))

    def read_authentication_exchange(self) -> AuthenticationExchange:
        """Receive exchange data during the authentication transaction.

        Returns:
            The exchange.
        """
        return self.read(AuthenticationExchange())

    def authentication_result(self) -> AuthenticationResult:
        """Receive an authentication result from the server.

        Returns:
            The result.
        """
        return self.read(AuthenticationResult())


class AsyncClient(HiSLIPClient):
    """An asynchronous connection to the HiSLIP server."""

    def __init__(self, host: str) -> None:
        """An asynchronous connection to the HiSLIP server.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)

    def async_initialize(self, session_id: int) -> AsyncInitializeResponse:
        """Initialize the asynchronous connection.

        Args:
            session_id: The session ID.

        Returns:
            The response.
        """
        self.write(AsyncInitialize(parameter=session_id))
        return self.read(AsyncInitializeResponse())

    def async_maximum_message_size(self, size: int) -> AsyncMaximumMessageSizeResponse:
        """Exchange the maximum message sizes that are accepted between the client and server.

        Args:
            size: The maximum message size that the client accepts.

        Returns:
            The maximum message size that the server accepts.
        """
        self.write(AsyncMaximumMessageSize(payload=pack("!Q", size)))
        msg = AsyncMaximumMessageSizeResponse()
        _ = self.read(msg)
        self.maximum_server_message_size: int = msg.maximum_message_size
        return msg

    def async_lock_request(self, timeout: float | None = None, lock_string: str = "") -> AsyncLockResponse:
        """Request a lock.

        Args:
            timeout: The number of seconds to wait to acquire a lock. A timeout of 0 indicates that
                the HiSLIP server should only grant the lock if it is available immediately.
            lock_string: An ASCII string that identifies this lock. If not specified, then an exclusive
                lock is requested, otherwise the string indicates an identification of a shared-lock request.
                The maximum length is 256 characters.

        Returns:
            The response.
        """
        if len(lock_string) > 256:  # noqa: PLR2004
            msg = "len(lock_string) > 256"
            raise ValueError(msg)

        socket_timeout = self.get_timeout()
        if timeout is None:
            timeout = ONE_DAY  # consider 1 day as "wait forever"
        self.set_timeout(10 + timeout)  # socket timeout must be larger
        timeout_ms = int(timeout * 1000)
        try:
            self.write(AsyncLock(1, timeout_ms, lock_string.encode("ascii")))
            return self.read(AsyncLockResponse())
        finally:
            self.set_timeout(socket_timeout)

    def async_lock_release(self, message_id: int) -> AsyncLockResponse:
        """Release a lock.

        Args:
            message_id: The most recent message id that was completed on the synchronous channel
                (i.e., `SyncClient.message_id`).

        Returns:
            The response.
        """
        self.write(AsyncLock(0, message_id))
        return self.read(AsyncLockResponse())

    def async_lock_info(self) -> AsyncLockInfoResponse:
        """Request the lock status from the HiSLIP server.

        Returns:
            The response.
        """
        self.write(AsyncLockInfo())
        return self.read(AsyncLockInfoResponse())

    def async_remote_local_control(self, request: int, message_id: int) -> AsyncRemoteLocalResponse:
        """Send a GPIB-like remote/local control request.

        Args:
            request: The request to perform.

                * 0 &mdash; Disable remote, `VI_GPIB_REN_DEASSERT`
                * 1 &mdash; Enable remote, `VI_GPIB_REN_ASSERT`
                * 2 &mdash; Disable remote and go to local, `VI_GPIB_REN_DEASSERT_GTL`
                * 3 &mdash; Enable Remote and go to remote, `VI_GPIB_REN_ASSERT_ADDRESS`
                * 4 &mdash; Enable remote and lock out local, `VI_GPIB_REN_ASSERT_LLO`
                * 5 &mdash; Enable remote, go to remote, and set local lockout, `VI_GPIB_REN_ASSERT_ADDRESS_LLO`
                * 6 &mdash; Go to local without changing REN or lockout state, `VI_GPIB_REN_ADDRESS_GTL`

            message_id: The most recent message id that was completed on the synchronous channel
                (i.e., `SyncClient.message_id`).

        Returns:
            The response.
        """
        self.write(AsyncRemoteLocalControl(request, message_id))
        return self.read(AsyncRemoteLocalResponse())

    def async_device_clear(self) -> AsyncDeviceClearAcknowledge:
        """Send the device clear request.

        Returns:
            The response.
        """
        self.write(AsyncDeviceClear())
        return self.read(AsyncDeviceClearAcknowledge())

    def async_status_query(self, synchronous: SyncClient) -> AsyncStatusResponse:
        """Status query transaction.

        The status query provides an 8-bit status response from the server that
        corresponds to the VISA `viReadSTB` operation.

        Args:
            synchronous: The synchronous client that corresponds with this asynchronous client.

        Returns:
            The response.
        """
        self.write(AsyncStatusQuery(synchronous.rmt, synchronous.message_id))
        return self.read(AsyncStatusResponse())

    def async_start_tls(self, synchronous: SyncClient) -> AsyncStartTLSResponse:
        """Initiate the secure connection transaction.

        Args:
            synchronous: The synchronous client that corresponds with this asynchronous client.

        Returns:
            The response.
        """
        payload = pack("!I", synchronous.message_id_received)
        self.write(AsyncStartTLS(synchronous.rmt, synchronous.message_id, payload))
        return self.read(AsyncStartTLSResponse())

    def async_end_tls(self, synchronous: SyncClient) -> AsyncEndTLSResponse:
        """Initiate the end of the secure connection transaction.

        Args:
            synchronous: The synchronous client that corresponds with this asynchronous client.

        Returns:
            The response.
        """
        payload = pack("!I", synchronous.message_id_received)
        self.write(AsyncEndTLS(synchronous.rmt, synchronous.message_id, payload))
        return self.read(AsyncEndTLSResponse())


class HiSLIP(MessageBased, regex=REGEX):
    """Base class for the HiSLIP communication protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for the [HiSLIP] communication protocol.

        [HiSLIP]: https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the HiSLIP communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Attributes: Connection Properties:
            buffer_size (int): The maximum number of bytes to read at a time. _Default: `4096`_
            lock_timeout (float): The timeout (in seconds) to wait for a lock (0 means wait forever). _Default: `0`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101

        info = parse_hislip_address(equipment.connection.address)
        if info is None:
            msg = f"Invalid HiSLIP address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._info: ParsedHiSLIPAddress = info

        # HiSLIP does not support termination characters
        self.write_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]
        self.read_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]

        props = equipment.connection.properties
        self._buffer_size: int = props.get("buffer_size", 4096)
        self._lock_timeout: float = props.get("lock_timeout", 0)
        self.lock_timeout = self._lock_timeout

        self._sync: SyncClient
        self._async: AsyncClient
        self._connect()
        self._set_interface_timeout()

    def _connect(self) -> None:
        def check_for_encryption(status: InitializeResponse) -> None:
            if status.encrypted or status.initial_encryption:
                self.disconnect()
                msg = "The HiSLIP server requires encryption, this feature has not been tested yet"
                raise RuntimeError(msg)

        host, port = self._info.host, self._info.port
        try:
            # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
            # 23 April 2020 (Revision 2.0)
            # Section 6.1: Initialization Transaction
            self._sync = SyncClient(host)
            self._sync.connect(port=port, timeout=self._timeout)

            status = self._sync.initialize(sub_address=self._info.name.encode())
            check_for_encryption(status)

            self._async = AsyncClient(host)
            self._async.connect(port=port, timeout=self._timeout)
            _ = self._async.async_initialize(status.session_id)

            r = self._async.async_maximum_message_size(self._max_read_size)
            self._sync.maximum_server_message_size = r.maximum_message_size
            self._async.maximum_server_message_size = r.maximum_message_size
        except (socket.timeout, TimeoutError):
            raise MSLTimeoutError(self) from None
        except Exception as e:  # noqa: BLE001
            msg = f"Cannot connect to {host}:{port}\n{e.__class__.__name__}: {e}"
            raise MSLConnectionError(self, msg) from None

    def _set_interface_max_read_size(self) -> None:  # pyright: ignore[reportImplicitOverride]
        if not hasattr(self, "_async"):
            return

        r = self._async.async_maximum_message_size(self._max_read_size)
        self._sync.maximum_server_message_size = r.maximum_message_size
        self._async.maximum_server_message_size = r.maximum_message_size

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if not hasattr(self, "_async"):
            return

        self._sync.set_timeout(self._timeout)
        self._async.set_timeout(self._timeout)

    @property
    def asynchronous(self) -> AsyncClient:
        """The reference to the asynchronous client."""
        return self._async

    @property
    def synchronous(self) -> SyncClient:
        """The reference to the synchronous client."""
        return self._sync

    @property
    def lock_timeout(self) -> float:
        """The time, in seconds, to wait to acquire a lock.

        Setting the value to &le;0 (or `None`) means _wait forever_.
        """
        if self._lock_timeout == ONE_DAY:
            return 0.0
        return self._lock_timeout

    @lock_timeout.setter
    def lock_timeout(self, value: float | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if value is None or value < 0:
            self._lock_timeout = ONE_DAY
        else:
            self._lock_timeout = float(value)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the connection to the HiSLIP server."""
        if not hasattr(self, "_async"):
            return

        if self._async.socket is None and self._sync.socket is None:
            return

        self._async.close()
        self._sync.close()
        super().disconnect()

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        try:
            return bytes(self._sync.receive(size=size, max_size=self._max_read_size, chunk_size=self._buffer_size))
        except HiSLIPError as e:
            # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
            # 23 April 2020 (Revision 2.0)
            # Section 6.2: Fatal Error Detection and Synchronization Recovery
            # If the error is detected by the client, after sending the FatalError
            # messages it shall close the HiSLIP connection
            self._send_fatal_error(e.message)
            raise
        except Exception as e:
            msg = FatalErrorMessage(payload=str(e).encode("ascii"))
            self._send_fatal_error(msg)
            raise

    def reconnect(self, max_attempts: int = 1) -> None:
        """Reconnect to the equipment.

        Args:
            max_attempts: The maximum number of attempts to try to reconnect with the equipment.
                If &lt;1, keep trying until a connection is successful. If the maximum number
                of attempts has been reached then an exception is raise.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._connect()
            except (MSLConnectionError, MSLTimeoutError):
                if 0 < max_attempts <= attempt:
                    raise

    def _send_fatal_error(self, message: Message) -> None:
        # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
        # 23 April 2020 (Revision 2.0)
        # Section 6.2: Fatal Error Detection and Synchronization Recovery
        # If the error is detected by the client, after sending the FatalError
        # messages it shall close the HiSLIP connection
        self._sync.write(message)
        self._async.write(message)
        self.disconnect()

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        try:
            return self._sync.send(message)
        except HiSLIPError as e:
            self._send_fatal_error(e.message)
            raise
        except Exception as e:
            msg = FatalErrorMessage(payload=str(e).encode("ascii"))
            self._send_fatal_error(msg)
            raise

    def read_stb(self) -> int:
        """Read the status byte from the device.

        Returns:
            The status byte.
        """
        reply = self._async.async_status_query(self._sync)
        return reply.status

    def trigger(self) -> None:
        """Send the trigger message (emulates a GPIB Group Execute Trigger event)."""
        self._sync.trigger()

    def clear(self) -> None:
        """Send the `clear` command to the device."""
        # IVI-6.1: IVI High-Speed LAN Instrument Protocol (HiSLIP)
        # 23 April 2020 (Revision 2.0)
        # Section 6.12: Device Clear Transaction
        #
        # This Connection class does not use the asynchronous client in an
        # asynchronous manner, therefore there should not be any pending
        # requests that need to be waited on to finish
        acknowledged = self._async.async_device_clear()
        _ = self._sync.device_clear_complete(acknowledged.feature_bitmap)

    def lock(self, lock_string: str = "") -> bool:
        """Acquire the device's lock.

        Args:
            lock_string: An ASCII string that identifies this lock. If not specified, then
                an exclusive lock is requested, otherwise the string indicates an
                identification of a shared-lock request.

        Returns:
            Whether acquiring the lock was successful.
        """
        status = self._async.async_lock_request(timeout=self._lock_timeout, lock_string=lock_string)
        return status.success

    def unlock(self) -> bool:
        """Release the lock acquired by [lock][msl.equipment.interfaces.hislip.HiSLIP.lock].

        Returns:
            Whether releasing the lock was successful.
        """
        status = self._async.async_lock_release(self._sync.message_id)
        return status.success

    def lock_status(self) -> tuple[bool, int]:
        """Request the lock status from the HiSLIP server.

        Returns:
            Whether the HiSLIP server has an exclusive lock with a client and
                the number of HiSLIP clients that have a lock with the HiSLIP server.
        """
        reply = self._async.async_lock_info()
        return reply.exclusive, reply.num_locks

    def remote_local_control(self, request: int) -> None:
        """Send a GPIB-like remote/local control request.

        Args:
            request: The request to perform.

                * 0 &mdash; Disable remote, `VI_GPIB_REN_DEASSERT`
                * 1 &mdash; Enable remote, `VI_GPIB_REN_ASSERT`
                * 2 &mdash; Disable remote and go to local, `VI_GPIB_REN_DEASSERT_GTL`
                * 3 &mdash; Enable Remote and go to remote, `VI_GPIB_REN_ASSERT_ADDRESS`
                * 4 &mdash; Enable remote and lock out local, `VI_GPIB_REN_ASSERT_LLO`
                * 5 &mdash; Enable remote, go to remote, and set local lockout, `VI_GPIB_REN_ASSERT_ADDRESS_LLO`
                * 6 &mdash; Go to local without changing REN or lockout state, `VI_GPIB_REN_ADDRESS_GTL`
        """
        _ = self._async.async_remote_local_control(request, self._sync.message_id)


@dataclass
class ParsedHiSLIPAddress:
    """The parsed result of a VISA-style address for the HiSLIP interface.

    Args:
        board: Board number.
        host: The IP address or hostname of the device.
        name: The LAN device name.
        port: The port number to open.
    """

    board: int
    host: str
    name: str
    port: int


def parse_hislip_address(address: str) -> ParsedHiSLIPAddress | None:
    """Parse the address for valid HiSLIP fields.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the HiSLIP interface.
    """
    match = REGEX.match(address)
    if not match:
        return None

    board = int(match["board"]) if match["board"] else 0
    port = int(match["port"]) if match["port"] else PORT
    return ParsedHiSLIPAddress(
        board=board,
        host=match["host"],
        name=match["name"],
        port=port,
    )
