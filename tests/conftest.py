"""Pytest configuration."""

from __future__ import annotations

import re
import socket
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer as BaseHTTPServer
from queue import Queue
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

import pytest
import zmq

from msl.equipment import Connection

if TYPE_CHECKING:
    from typing import Any, TypeVar

    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket

    # the Self type was added in Python 3.11 (PEP 673)
    # using TypeVar is equivalent for < 3.11
    HTTPSelf = TypeVar("HTTPSelf", bound="HTTPServer")
    TCPSelf = TypeVar("TCPSelf", bound="TCPServer")
    UDPSelf = TypeVar("UDPSelf", bound="UDPServer")
    ZMQSelf = TypeVar("ZMQSelf", bound="ZMQServer")


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler."""

    queue: Queue[tuple[int, bytes]] = Queue()

    def do_GET(self) -> None:
        """Handle a GET request."""
        code, message = (200, b"") if self.queue.empty() else self.queue.get()
        self.send_response(code)
        self.end_headers()
        if message:
            _ = self.wfile.write(message)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, ANN401  # pyright: ignore[reportImplicitOverride]
        """Overrides: http.server.BaseHTTPRequestHandler.log_message.

        Ignore all log messages from being displayed in `sys.stdout`.
        """


class HTTPServer:
    """HTTP server."""

    def __init__(self, *, host: str = "127.0.0.1", port: int = 0) -> None:
        """HTTP server.

        Args:
            host: The host to run the server on.
            port: The port number to use for the server.
        """
        self.clear_response_queue()
        self._server: BaseHTTPServer = BaseHTTPServer((host, port), HTTPRequestHandler)
        self._thread: Thread | None = None

    def __enter__(self: HTTPSelf) -> HTTPSelf:  # noqa: PYI019
        """Enter a context manager."""
        self.start()
        return self

    def __exit__(self, *ignored: object) -> None:
        """Exit the context manager."""
        self.stop()

    def add_response(self, content: bytes = b"", code: int = 200) -> None:
        """Add a response to the server's queue.

        Args:
            content: The content of the response message.
            code: The HTTP status code.
        """
        HTTPRequestHandler.queue.put((code, content))

    def clear_response_queue(self) -> None:
        """Clear the server's response queue."""
        with HTTPRequestHandler.queue.mutex:
            HTTPRequestHandler.queue.queue.clear()

    @property
    def host(self) -> str:
        """Returns the host that the server is running on."""
        return str(self._server.server_address[0])

    @property
    def port(self) -> int:
        """Returns the port number of the server."""
        return self._server.server_port

    def start(self, wait: float = 0.1) -> None:
        """Start the server.

        Args:
            wait: The number of seconds to wait for the server to start before returning.
        """
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return
        self._server.shutdown()
        self._thread.join()
        self._thread = None
        self.clear_response_queue()


class TCPServer:
    """A TCP socket server."""

    def __init__(self, *, host: str = "127.0.0.1", port: int = 0, term: bytes = b"\n") -> None:
        """A TCP socket server.

        Args:
            host: The host to run the server on.
            port: The port number to use for the server.
            term: The termination character(s) to use for messages.
        """
        self.term: bytes = term
        self._thread: Thread | None = None
        self._queue: Queue[bytes] = Queue()
        self._conn: socket.socket | None = None
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, port))
        self._sock.listen(1)

    def __enter__(self: TCPSelf) -> TCPSelf:  # noqa: PYI019
        """Enter a context manager."""
        self.start()
        return self

    def __exit__(self, *ignored: object) -> None:
        """Exit the context manager."""
        self.stop()

    def add_response(self, content: bytes) -> None:
        """Add a response to the server's queue.

        Args:
            content: The content of the response message.
        """
        self._queue.put(content)

    def clear_response_queue(self) -> None:
        """Clear the server's response queue."""
        with self._queue.mutex:
            self._queue.queue.clear()

    @property
    def host(self) -> str:
        """Returns the host that the server is running on."""
        return str(self._sock.getsockname()[0])

    @property
    def port(self) -> int:
        """Returns the port number of the server."""
        return int(self._sock.getsockname()[1])

    def start(self, wait: float = 0.1) -> None:
        """Start a TCP server.

        Args:
            wait: The number of seconds to wait for the server to start before returning.
        """

        def _start(term: bytes) -> None:
            self._conn, _ = self._sock.accept()
            while True:
                data = bytearray()
                while True:
                    try:
                        data.extend(self._conn.recv(4096))
                    except (ConnectionResetError, ConnectionAbortedError):
                        break

                    if not data or data.endswith(term):
                        break

                if not data or data.startswith(b"SHUTDOWN"):
                    break

                self._conn.sendall(data if self._queue.empty() else self._queue.get())

        self._thread = Thread(target=_start, args=(self.term,), daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return

        if self._conn is None:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.connect((self.host, self.port))

        self._conn.sendall(b"SHUTDOWN" + self.term)

        self._thread.join()
        self._thread = None

        self._conn.close()
        self._sock.close()
        self.clear_response_queue()


class UDPServer:
    """A UDP socket server."""

    def __init__(self, *, host: str = "127.0.0.1", port: int = 0, term: bytes = b"\n") -> None:
        """A UDP socket server.

        Args:
            host: The host to run the server on.
            port: The port number to use for the server.
            term: The termination character(s) to use for messages.
        """
        self.term: bytes = term
        self._thread: Thread | None = None
        self._queue: Queue[bytes] = Queue()
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((host, port))

    def __enter__(self: UDPSelf) -> UDPSelf:  # noqa: PYI019
        """Enter a context manager."""
        self.start()
        return self

    def __exit__(self, *ignored: object) -> None:
        """Exit the context manager."""
        self.stop()

    def add_response(self, content: bytes) -> None:
        """Add a response to the server's queue.

        Args:
            content: The content of the response message.
        """
        self._queue.put(content)

    def clear_response_queue(self) -> None:
        """Clear the server's response queue."""
        with self._queue.mutex:
            self._queue.queue.clear()

    @property
    def host(self) -> str:
        """Returns the host that the server is running on."""
        return str(self._sock.getsockname()[0])

    @property
    def port(self) -> int:
        """Returns the port number of the server."""
        return int(self._sock.getsockname()[1])

    def start(self, wait: float = 0.1) -> None:
        """Start a TCP server.

        Args:
            wait: The number of seconds to wait for the server to start before returning.
        """

        def _start(term: bytes) -> None:
            addr = ("", 0)
            while True:
                data = bytearray()
                while True:
                    msg, addr = self._sock.recvfrom(65536)
                    data.extend(msg)
                    if not data or data.endswith(term):
                        break

                if not data or data.startswith(b"SHUTDOWN"):
                    break

                msg = bytes(data) if self._queue.empty() else self._queue.get()
                _ = self._sock.sendto(msg, addr)

        self._thread = Thread(target=_start, args=(self.term,), daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conn:
            conn.connect((self.host, self.port))
            conn.sendall(b"SHUTDOWN" + self.term)

        self._thread.join()
        self._thread = None

        self._sock.close()
        self.clear_response_queue()


class ZMQServer:
    """A ZeroMQ server."""

    def __init__(self, *, host: str = "127.0.0.1", port: int = 0) -> None:
        """A ZeroMQ server.

        Args:
            host: The host to run the server on.
            port: The port number to use for the server.
        """
        self._thread: Thread | None = None
        self._queue: Queue[bytes] = Queue()
        self._context: Context[SyncSocket] = zmq.Context()
        self._socket: SyncSocket = self._context.socket(zmq.REP)

        bound = self._socket.bind(f"tcp://{host}:{port}")
        address = re.match(r"tcp://(?P<host>[^\s:]+):(?P<port>\d+)", bound.addr)
        assert address is not None, "Invalid regex for ZMQ address"
        self._host: str = address["host"]
        self._port: int = int(address["port"])

    def __enter__(self: ZMQServer) -> ZMQServer:  # noqa: PYI034
        """Enter a context manager."""
        self.start()
        return self

    def __exit__(self, *ignored: object) -> None:
        """Exit the context manager."""
        self.stop()

    def add_response(self, content: bytes) -> None:
        """Add a response to the server's queue.

        Args:
            content: The content of the response message.
        """
        self._queue.put(content)

    def clear_response_queue(self) -> None:
        """Clear the server's response queue."""
        with self._queue.mutex:
            self._queue.queue.clear()

    @property
    def host(self) -> str:
        """Returns the host that the server is running on."""
        return self._host

    @property
    def port(self) -> int:
        """Returns the port number of the server."""
        return self._port

    def start(self, wait: float = 0.1) -> None:
        """Start a ZeroMQ server.

        Args:
            wait: The number of seconds to wait for the server to start before returning.
        """

        def _start() -> None:
            while True:
                data = self._socket.recv()
                if data == b"SHUTDOWN":
                    break

                self._socket.send(data if self._queue.empty() else self._queue.get())

        self._thread = Thread(target=_start, daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return

        c = Connection(f"ZMQ::{self._host}::{self._port}")
        with c.connect() as dev:
            dev.write(b"SHUTDOWN")

        self._thread.join()
        self._thread = None

        self._socket.unbind(f"tcp://{self._host}:{self._port}")
        self._context.destroy()
        self.clear_response_queue()


@pytest.fixture
def http_server() -> type[HTTPServer]:
    return HTTPServer


@pytest.fixture
def tcp_server() -> type[TCPServer]:
    return TCPServer


@pytest.fixture
def udp_server() -> type[UDPServer]:
    return UDPServer


@pytest.fixture
def zmq_server() -> type[ZMQServer]:
    return ZMQServer
