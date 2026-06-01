"""Base class for equipment that use the ZeroMQ communication protocol."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple, overload

import zmq

from msl.equipment.utils import to_enum

from .message import Message, MSLConnectionError

if TYPE_CHECKING:
    from typing import Literal

    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket
    from zmq.sugar.tracker import MessageTracker

    from msl.equipment.schema import Equipment
    from msl.equipment.typing import ZMQMultiPart


REGEX = re.compile(r"^ZMQ::(?P<host>[^\s:]+)::(?P<port>\d+)", flags=re.IGNORECASE)


class ZeroMQ(Message, regex=REGEX):
    """Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the [ZeroMQ](https://zeromq.org/) communication protocol, as well as the _properties_
        defined in [Message][msl.equipment.interfaces.message.Message].
        The [ZeroMQ](https://zeromq.org/) protocol does not use termination characters, so if
        termination characters are specified the value is ignored and is set to `None`.

        Attributes: Connection Properties:
            protocol (str): ZeroMQ protocol (`tcp`, `udp`, `pgm`, `inproc`, `ipc`) _Default: `tcp`_
            socket_type (int | str | zmq.SocketType): ZeroMQ socket type. Can also be a
                [SocketType][zmq.SocketType] enum member name (case insensitive) or value.
                _Default: `REQ`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101

        address = parse_zmq_address(equipment.connection.address)
        if address is None:
            msg = f"Invalid ZeroMQ address {equipment.connection.address!r}"
            raise ValueError(msg)

        p = equipment.connection.properties
        socket_type = to_enum(p.get("socket_type", "REQ"), zmq.SocketType, to_upper=True)
        protocol: str = p.get("protocol", "tcp")

        # ZeroMQ does not use termination characters
        self._read_termination: bytes | None = None
        self._write_termination: bytes | None = None

        self._context: Context[SyncSocket] = zmq.Context()
        self._socket: SyncSocket = self._context.socket(socket_type)
        self._set_interface_timeout()
        self._set_interface_max_read_size()

        # For most ZMQ transports and socket types the connection is not performed immediately
        # but only as needed by ZMQ. Thus a successful call to zmq.Socket.connect() does not mean
        # that the connection was or could actually be established to a device at `host:port`.
        # Because of this, for most transports and socket types the order in which a server
        # socket is bound (i.e., the equipment is turned on) and a client socket is connected
        # to it does not matter. A zmq.ZMQError raised here would only be if the `protocol`
        # is not supported for the operating system
        try:
            _ = self._socket.connect(f"{protocol}://{address.host}:{address.port}")
        except zmq.ZMQError as e:
            msg = f"{e.__class__.__name__}: {e}"
            raise MSLConnectionError(self, msg) from None

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in `Message`."""
        reply = self._socket.recv(flags=0, copy=True)
        if size is None:
            return reply
        return reply[:size]

    def _set_interface_max_read_size(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in `Message`."""
        if hasattr(self, "_socket"):
            self._socket.setsockopt(zmq.MAXMSGSIZE, self.max_read_size)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in `Message`."""
        if hasattr(self, "_socket"):
            # ZeroMQ requires the timeout to be an integer with units of milliseconds (-1 is Infinity)
            timeout_ms = -1 if self._timeout is None else int(self._timeout * 1000)
            self._socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
            self._socket.setsockopt(zmq.SNDTIMEO, timeout_ms)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in `Message`."""
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

    @overload
    def read_multipart(self, flags: int = ..., *, copy: Literal[True], track: bool = ...) -> list[bytes]: ...

    @overload
    def read_multipart(self, flags: int = ..., *, copy: Literal[False], track: bool = ...) -> list[zmq.Frame]: ...

    @overload
    def read_multipart(self, flags: int = ..., *, track: bool = ...) -> list[bytes]: ...

    def read_multipart(
        self, flags: int = 0, *, copy: bool = True, track: bool = False
    ) -> list[zmq.Frame] | list[bytes]:
        """Read a multipart message.

        Args:
            flags: The only supported flag is [DONTWAIT][zmq.Flag.DONTWAIT]
                (which has a `zmq.NOBLOCK` alias).
            copy: Should the message frame(s) be received in a copying or non-copying manner?
                If `False` a [Frame][zmq.Frame] object is returned for each part, if `True` a
                copy of the bytes is made for each frame.
            track: Should the message frame(s) be tracked for notification that ZeroMQ has
                finished with it? (ignored if `copy=True`)

        Returns:
            If `copy=True` returns a [list][][[bytes][]], otherwise a [list][][[Frame][zmq.Frame]].
        """
        return self._socket.recv_multipart(flags=flags, copy=copy, track=track)

    @property
    def socket(self) -> SyncSocket:
        """Returns a reference to the underlying socket."""
        return self._socket

    @overload
    def write_multipart(
        self, msg_parts: ZMQMultiPart, *, flags: int = ..., copy: Literal[True], track: bool = ...
    ) -> None: ...

    @overload
    def write_multipart(
        self, msg_parts: ZMQMultiPart, *, flags: int = ..., copy: Literal[False], track: bool = ...
    ) -> zmq.MessageTracker: ...

    @overload
    def write_multipart(self, msg_parts: ZMQMultiPart, *, flags: int = ..., track: bool = ...) -> None: ...

    def write_multipart(
        self,
        msg_parts: ZMQMultiPart,
        *,
        flags: int = 0,
        copy: bool = True,
        track: bool = False,
    ) -> MessageTracker | None:
        """Write a multipart message.

        Args:
            msg_parts: A sequence of objects to send as a multipart message.
            flags: The only supported flags are [DONTWAIT][zmq.Flag.DONTWAIT]
                (which has a `zmq.NOBLOCK` alias), [SNDMORE][zmq.Flag.SNDMORE]
                or a union of `NOBLOCK|SNDMORE`.

                !!! note
                    The [SNDMORE][zmq.Flag.SNDMORE] flag is automatically added to each
                    message part before the last message.

            copy: Should the frame(s) be sent in a copying or non-copying manner?
                If `False`, frames smaller than [copy_threshold][zmq.Socket.copy_threshold]
                bytes are copied anyway.
            track: Should the frame(s) be tracked for notification that ZeroMQ has
                finished with it (ignored if `copy=True`)?

        Returns:
            If `copy=True` returns `None`, otherwise a [MessageTracker][zmq.MessageTracker] object
                that will have its [done][zmq.MessageTracker.done] property be `False` until
                the last write is completed.
        """
        out: MessageTracker | None = self._socket.send_multipart(msg_parts, flags=flags, copy=copy, track=track)  # pyright: ignore[reportUnknownMemberType]
        return out


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
