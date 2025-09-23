"""Base class for equipment that use the ZeroMQ communication protocol."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple

import zmq
from zmq.constants import SocketType

from msl.equipment.utils import to_enum

from .message_based import MessageBased, MSLConnectionError

if TYPE_CHECKING:
    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket

    from msl.equipment.schema import Equipment


REGEX = re.compile(r"ZMQ::(?P<host>[^\s:]+)::(?P<port>\d+)", flags=re.IGNORECASE)


class ZeroMQ(MessageBased, regex=REGEX):
    """Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the [ZeroMQ](https://zeromq.org/) communication protocol, as well as the _properties_
        defined in [MessageBased][msl.equipment.interfaces.message_based.MessageBased].
        The [ZeroMQ](https://zeromq.org/) protocol does not use termination characters, so if
        termination characters are specified the value is ignored and is set to `None`.

        Attributes: Connection Properties:
            protocol (str): ZeroMQ protocol (`tcp`, `udp`, `pgm`, `inproc`, `ipc`) _Default: `tcp`_
            socket_type (int | str): ZeroMQ [socket type][zmq.SocketType]. _Default: `REQ`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101

        address = parse_zmq_address(equipment.connection.address)
        if address is None:
            msg = f"Invalid ZeroMQ address {equipment.connection.address!r}"
            raise ValueError(msg)

        p = equipment.connection.properties
        socket_type = to_enum(p.get("socket_type", "REQ"), SocketType, to_upper=True)
        protocol: str = p.get("protocol", "tcp")

        # ZeroMQ does not use termination characters
        self.read_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]
        self.write_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]

        self._context: Context[SyncSocket] = zmq.Context()
        self._socket: SyncSocket = self._context.socket(socket_type)
        self._set_interface_timeout()
        self._set_interface_max_read_size()

        # Calling zmq.Socket.connect() does not verify that the host:port value until the
        # socket is used to write/read bytes. An error raised here would be for an an invalid
        # ZeroMQ addr value
        try:
            _ = self._socket.connect(f"{protocol}://{address.host}:{address.port}")
        except zmq.ZMQError as e:
            msg = f"{e.__class__.__name__}: {e}"
            raise MSLConnectionError(self, msg) from None

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        reply = self._socket.recv(flags=0, copy=True)
        if size is None:
            return reply
        return reply[:size]

    def _set_interface_max_read_size(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if hasattr(self, "_socket"):
            self._socket.setsockopt(zmq.MAXMSGSIZE, self.max_read_size)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if hasattr(self, "_socket"):
            # ZeroMQ requires the timeout to be an integer with units of milliseconds (-1 is Infinity)
            timeout_ms = -1 if self._timeout is None else int(self._timeout * 1000)
            self._socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
            self._socket.setsockopt(zmq.SNDTIMEO, timeout_ms)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        self._socket.send(message, flags=0, copy=True)
        return len(message)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the socket connection and terminate the context."""
        if hasattr(self, "_socket") and not self._socket.closed:
            self._context.set(zmq.BLOCKY, 0)
            self._socket.setsockopt(zmq.LINGER, 0)
            self._socket.close()
            self._context.term()
            super().disconnect()

    @property
    def socket(self) -> SyncSocket:
        """Returns a reference to the underlying socket."""
        return self._socket


class ParsedZMQAddress(NamedTuple):
    """The parsed result of a VISA-style address for the ZeroMQ interface.

    Args:
        host: Host address.
        port: Port number.
    """

    host: str
    port: int


def parse_zmq_address(address: str) -> ParsedZMQAddress | None:
    """Parse the address for valid ZeroMQ fields.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the ZeroMQ interface.
    """
    match = REGEX.match(address)
    return ParsedZMQAddress(match["host"], int(match["port"])) if match else None
