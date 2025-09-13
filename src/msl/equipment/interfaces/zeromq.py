"""Base class for equipment that use the ZeroMQ communication protocol."""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

import zmq
from zmq.constants import SocketType

from msl.equipment.exceptions import MSLConnectionError
from msl.equipment.utils import to_enum

from .message_based import MessageBased, MSLTimeoutError

if TYPE_CHECKING:
    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket

    from msl.equipment.schema import Equipment


REGEX_ZMQ = re.compile(r"ZMQ::(?P<host>[^\s:]+)::(?P<port>\d+)", flags=re.IGNORECASE)


class ZeroMQ(MessageBased, regex=REGEX_ZMQ):
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
        assert equipment.connection is not None  # noqa: S101
        p = equipment.connection.properties

        # ZeroMQ does not use termination characters
        p["termination"] = None

        super().__init__(equipment)

        address = parse_zmq_address(equipment.connection.address)
        if address is None:
            msg = f"Invalid ZeroMQ address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._address: ParsedZMQAddress = address

        self._socket_type: SocketType = to_enum(p.get("socket_type", "REQ"), SocketType, to_upper=True)
        self._protocol: str = p.get("protocol", "tcp")

        self._context: Context[SyncSocket] = zmq.Context()
        self._socket: SyncSocket = self._context.socket(self._socket_type)
        self._connect()

    def _connect(self) -> None:
        host, port = self._address.host, self._address.port
        # Calling zmq.Socket.connect() does not verify if the connection can be made immediately
        # Use the builtin socket module to verify
        try:
            with socket.socket() as s:
                s.settimeout(self.timeout or 10)
                s.connect((host, port))
        except (OSError, TimeoutError):
            raise MSLTimeoutError(self) from None

        try:
            # The (host, port) is valid, connect with ZeroMQ
            _ = self._socket.connect(f"{self._protocol}://{host}:{port}")
        except zmq.ZMQError as e:
            raise MSLConnectionError(self, str(e)) from None

        self._set_interface_timeout()

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        reply = self._socket.recv(flags=0, copy=True)
        if size is None:
            return reply
        return reply[:size]

    def _set_interface_max_read_size(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if not hasattr(self, "_socket"):
            return
        self._socket.setsockopt(zmq.MAXMSGSIZE, self.max_read_size)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if not hasattr(self, "_socket"):
            return

        # ZeroMQ requires the timeout to be an integer with units of milliseconds (-1 is Infinity)
        timeout_ms = -1 if self._timeout is None else int(self._timeout * 1000)
        self._socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self._socket.setsockopt(zmq.SNDTIMEO, timeout_ms)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        self._socket.send(message, flags=0, copy=True)
        return len(message)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the socket connection."""
        if hasattr(self, "_socket"):
            self._socket.close()
            self._context.term()
        super().disconnect()


@dataclass
class ParsedZMQAddress:
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
    match = REGEX_ZMQ.match(address)
    return ParsedZMQAddress(match["host"], int(match["port"])) if match else None
