"""Base class for equipment that is connected through a socket."""

from __future__ import annotations

import re
import socket
import time
from typing import TYPE_CHECKING, NamedTuple

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"(?P<prefix>TCP|UDP|TCPIP\d*)::(?P<host>[^\s:]+)::(?P<port>\d+)(?P<suffix>::SOCKET)?", flags=re.IGNORECASE
)


class Socket(MessageBased, regex=REGEX):
    """Base class for equipment that is connected through a socket."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that is connected through a socket.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the socket communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Attributes: Connection Properties:
            buffer_size (int): The maximum number of bytes to read at a time. _Default: `4096`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101

        info = parse_socket_address(equipment.connection.address)
        if info is None:
            msg = f"Invalid socket address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._info: ParsedSocketAddress = info

        props = equipment.connection.properties
        self._buffer_size: int = props.get("buffer_size", 4096)
        self._byte_buffer: bytearray = bytearray()

        typ: int = socket.SOCK_DGRAM if equipment.connection.address.startswith("UDP") else socket.SOCK_STREAM
        self._is_stream: bool = typ == socket.SOCK_STREAM
        self._socket: socket.socket = socket.socket(family=socket.AF_INET, type=typ)
        self._connect()

    def _connect(self) -> None:
        # it is recommended to set the timeout before calling connect()
        self._set_interface_timeout()
        if self._is_stream:
            try:
                self._socket.connect(self._info)
            except (socket.timeout, TimeoutError):
                raise MSLTimeoutError(self) from None
            except OSError as e:
                host, port = self._info
                msg = f"Cannot connect to {host}:{port}\n{e.__class__.__name__}: {e}"
                raise MSLConnectionError(self, msg) from None

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]  # noqa: C901
        """Overrides method in MessageBased."""
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
                error = f"len(message) [{len(self._byte_buffer)}] > max_read_size [{self._max_read_size}]"
                raise RuntimeError(error)

            elapsed_time = time.time() - t0
            if self._timeout and (elapsed_time > self._timeout):
                self._socket.settimeout(original_timeout)
                raise MSLTimeoutError(self)

            # decrease the timeout when reading each chunk so that the total
            # time to receive all data preserves what was specified
            if original_timeout is not None:
                self._socket.settimeout(max(0, original_timeout - elapsed_time))

        self._socket.settimeout(original_timeout)
        return bytes(msg)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if hasattr(self, "_socket"):
            self._socket.settimeout(self._timeout)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if self._is_stream:
            self._socket.sendall(message)
        else:
            _ = self._socket.sendto(message, self._info)
        return len(message)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the socket."""
        if hasattr(self, "_socket") and self._socket.fileno() != -1:
            self._socket.close()
            super().disconnect()

    def reconnect(self, max_attempts: int = 1) -> None:
        """Reconnect to the equipment.

        Args:
            max_attempts: The maximum number of attempts to try to reconnect with the equipment.
                If &lt;1, keep trying until a connection is successful. If the maximum number
                of attempts has been reached then an exception is raise.
        """
        self._socket.close()
        self._socket = socket.socket(family=self._socket.family, type=self._socket.type)

        attempt = 0
        while True:
            attempt += 1
            try:
                return self._connect()
            except (MSLConnectionError, MSLTimeoutError):
                if 0 < max_attempts <= attempt:
                    raise

    @property
    def socket(self) -> socket.socket:
        """Returns a reference to the underlying socket."""
        return self._socket


class ParsedSocketAddress(NamedTuple):
    """The parsed result of a VISA-style address for the socket interface.

    Args:
        host: Host address.
        port: Port number.
    """

    host: str
    port: int


def parse_socket_address(address: str) -> ParsedSocketAddress | None:
    """Get the host and port from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the Socket interface.
    """
    match = REGEX.match(address)
    if match is None:
        return None

    # check the IVI format
    if match["prefix"].startswith("TCPIP") and match["suffix"] != "::SOCKET":
        return None

    return ParsedSocketAddress(match["host"], int(match["port"]))
