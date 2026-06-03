"""Base class for equipment that use the ZeroMQ communication protocol."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple, overload

import zmq
import zmq.asyncio

from msl.equipment.utils import to_enum

from .message import Message, MSLConnectionError

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Literal

    from zmq.auth.asyncio import AsyncioAuthenticator
    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket
    from zmq.sugar.tracker import MessageTracker

    from msl.equipment.schema import Equipment
    from msl.equipment.typing import ZMQBuffer, ZMQServerResponse


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
                If `False`, a [Frame][zmq.Frame] object is returned for each message part,
                otherwise a copy of the bytes is made for each frame.
            track: Should the message frame(s) be tracked for notification that ZeroMQ has
                finished with it? Ignored if `copy=True`.

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
        self, msg_parts: Sequence[ZMQBuffer], *, flags: int = ..., copy: Literal[True], track: bool = ...
    ) -> None: ...

    @overload
    def write_multipart(
        self, msg_parts: Sequence[ZMQBuffer], *, flags: int = ..., copy: Literal[False], track: bool = ...
    ) -> zmq.MessageTracker: ...

    @overload
    def write_multipart(self, msg_parts: Sequence[ZMQBuffer], *, flags: int = ..., track: bool = ...) -> None: ...

    def write_multipart(
        self,
        msg_parts: Sequence[ZMQBuffer],
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

            copy: Should the message frame(s) be sent in a copying or non-copying manner?
                If `False`, messages smaller than [copy_threshold][zmq.Socket.copy_threshold]
                bytes are copied anyway.
            track: Should the message frame(s) be tracked for notification that ZeroMQ has
                finished with it? Ignored if `copy=True`.

        Returns:
            If `copy=True` returns `None`, otherwise a [MessageTracker][zmq.MessageTracker] object
                that will have its [done][zmq.MessageTracker.done] property be `False` until
                the last write has completed.
        """
        out: MessageTracker | None = self._socket.send_multipart(msg_parts, flags=flags, copy=copy, track=track)  # pyright: ignore[reportUnknownMemberType]
        return out


class ZeroMQServer(ABC):
    """Start a server to handle requests for the [ZeroMQ](https://zeromq.org/) protocol.

    This class is useful if you would like to allow equipment that has a non-Ethernet interface
    (e.g., GPIB, RS-232, USB) to be controllable from any computer that is on the network.

    See [here][equipment-server] for examples on how to use this class.
    """

    def __init__(
        self,
        *,
        allow: str | Iterable[str] | None = None,
        host: str = "*",
        port: int = 0,
        protocol: str = "tcp",
        socket_type: int | str | zmq.SocketType = "REP",
    ) -> None:
        """Start a server to handle requests for the [ZeroMQ](https://zeromq.org/) protocol.

        Args:
            allow: The IPv4 address(es), or hostname(s), that are allowed to connect to the server.
                If not specified, all IP addresses can connect. If a hostname cannot be resolved
                to an IPv4 address a [gaierror][socket.gaierror] is raised, in which case you must
                explicitly specify the IPv4 address instead of the hostname.
            host: The network interface (IP address) to bind the server to. If `*`, the server
                listens on all available network interfaces simultaneously.
            port: The port to bind the server to. If `0`, binds the server to any available port.
            protocol: The ZeroMQ protocol to use (`tcp`, `udp`, `pgm`, `inproc`, `ipc`).
            socket_type: The ZeroMQ socket type. Can also be a [SocketType][zmq.SocketType] enum
                member name (case insensitive) or value.
        """
        self._auth: AsyncioAuthenticator | None = None
        self._interrupt: _Interrupter = _Interrupter()

        self.context: zmq.asyncio.Context = zmq.asyncio.Context()
        """[Context][zmq.asyncio.Context] &mdash; The asynchronous ZeroMQ context."""

        self._socket_type: zmq.SocketType = to_enum(socket_type, zmq.SocketType, to_upper=True)

        self.socket: zmq.asyncio.Socket = self.context.socket(self._socket_type)
        """[Socket][zmq.asyncio.Socket] &mdash; The asynchronous ZeroMQ socket."""

        if allow:
            from socket import gethostbyname  # noqa: PLC0415

            from zmq.auth.asyncio import AsyncioAuthenticator  # noqa: PLC0415

            if isinstance(allow, str):
                allow = [allow]

            self._auth = AsyncioAuthenticator(self.context)
            self._auth.allow(*{gethostbyname(item) for item in allow})

        self.port: int = port
        """[int][] &mdash; The port number that the server is running on.

        If a value of `0` is used to instantiate the class, the port value will become
        non-zero once [start][msl.equipment.interfaces.zeromq.ZeroMQServer.start]
        is called.
        """

        address = f"{protocol}://{host}"
        if port > 0:
            address += f":{port}"

        self.address: str = address
        """[str][] &mdash; The ZeroMQ address that the server is using, i.e., `protocol://host:port`.

        The value is updated once [start][msl.equipment.interfaces.zeromq.ZeroMQServer.start] is called.
        """

        self._poller: zmq.asyncio.Poller = zmq.asyncio.Poller()
        self._poller.register(self.socket, zmq.POLLIN)
        self._poller.register(self._interrupt.aborter, zmq.POLLIN)

    def __del__(self) -> None:
        """Calls `_shutdown`."""
        self._shutdown()

    def _shutdown(self) -> None:
        """Shut down the server."""
        if self._auth is not None:
            self._auth.stop()
            self._auth = None
        if hasattr(self, "address") and self.address and not self.socket.closed:
            self._poller.unregister(self.socket)
            self._poller.unregister(self._interrupt.aborter)
            self.socket.unbind(self.address)
        self._interrupt.shutdown()
        self.context.destroy()

    async def _start(self, *, info: bool) -> None:
        """Start the server."""
        from zmq.utils.win32 import allow_interrupt  # noqa: PLC0415

        # Must be called before bind, requires an asyncio event loop to be running
        if self._auth is not None:
            self._auth.start()
            self.socket.zap_domain = b"global"

        if self.port <= 0:
            self.port = self.socket.bind_to_random_port(self.address)
        else:
            _ = self.socket.bind(self.address)

        self.address = self.socket.getsockopt_string(zmq.LAST_ENDPOINT)

        if info:
            msg = (
                f"{self.__class__.__name__} running on {self.address!r} using a {self._socket_type.name!r} socket\n"
                "Press Ctrl+C to shut down the server"
            )
            print(msg)  # noqa: T201

        p = self._poller
        s = self.socket
        with allow_interrupt(self._interrupt):
            while True:
                socks = dict(await p.poll())
                if socks.get(s) == zmq.POLLIN:
                    request = await s.recv_multipart()
                    reply = self.handle_request(request)
                    if reply is None:
                        pass
                    elif hasattr(reply, "__buffer__"):
                        _ = await s.send(reply)
                    else:
                        _ = await s.send_multipart(reply)  # pyright: ignore[reportUnknownMemberType, reportArgumentType]
                else:
                    break

    @abstractmethod
    def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:
        """Handle a *single* request.

        !!! warning "Attention"
            You must override this method.

        Args:
            msg_parts: The request message. A client can choose to write a request using the
                [write_multipart][msl.equipment.interfaces.zeromq.ZeroMQ.write_multipart]
                method to clearly separate different parts of the request message for the
                server to process, e.g., separating the name of the function to call from
                the function parameters.

        Returns:
            The response. Can be one or more objects that support the buffer protocol or
                `None` (do not send a response). A server cannot return `None` when using the
                [REQ][zmq.SocketType.REQ] (client) and [REP][zmq.SocketType.REP] (server)
                socket types since a client must always read the response after sending
                a request. Return empty bytes (`b""`) instead of `None` in this case.
        """

    def start(self, *, info: bool = True) -> None:
        """Start the server.

        Args:
            info: Whether to print information about the running server.
        """
        import asyncio  # noqa: PLC0415
        import sys  # noqa: PLC0415

        try:
            if sys.version_info < (3, 12):
                if sys.platform == "win32":  # pyright: ignore[reportUnreachable]
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(self._start(info=info))
            else:
                asyncio.run(self._start(info=info), loop_factory=asyncio.SelectorEventLoop)
        except KeyboardInterrupt:  # pragma: no cover
            pass
        finally:
            self.shutdown_handler()
            self._shutdown()

    def shutdown_handler(self) -> None:
        """You can override this method in the subclass to perform any necessary clean up.

        This method is called after [start][msl.equipment.interfaces.zeromq.ZeroMQServer.start]
        finishes but before the [socket][msl.equipment.interfaces.zeromq.ZeroMQServer.socket] is
        unbound and the [context][msl.equipment.interfaces.zeromq.ZeroMQServer.context] is terminated.
        """
        return

    def shutdown_server(self) -> None:
        """Shut down the server.

        Pressing `Ctrl+C` in the terminal that the server is running in will also shut down the server.
        """
        self._interrupt()


class _Interrupter:
    """Handle Ctrl+C on Windows."""

    def __init__(self) -> None:
        self.context: Context[SyncSocket] = zmq.Context()

        self.publisher: SyncSocket = self.context.socket(zmq.PUB)
        _ = self.publisher.bind("inproc://ctrl+c")

        self.aborter: SyncSocket = self.context.socket(zmq.SUB)
        self.aborter.setsockopt(zmq.SUBSCRIBE, b"")
        _ = self.aborter.connect("inproc://ctrl+c")

    def __call__(self) -> None:
        self.publisher.send(b"")

    def shutdown(self) -> None:
        self.publisher.close()
        self.aborter.close()
        self.context.destroy()


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
