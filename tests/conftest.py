"""Pytest configuration."""

from __future__ import annotations

import contextlib
import os
import socket
import sys
from array import array
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer as BaseHTTPServer
from queue import Queue
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

import pytest
import usb  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import zmq
from usb.backend import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    IBackend,  # pyright: ignore[reportUnknownVariableType]
)

from msl.equipment import Connection

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any, TypeVar

    from zmq.sugar.context import Context
    from zmq.sugar.socket import SyncSocket

    # the Self type was added in Python 3.11 (PEP 673)
    # using TypeVar is equivalent for < 3.11
    HTTPSelf = TypeVar("HTTPSelf", bound="HTTPServer")
    TCPSelf = TypeVar("TCPSelf", bound="TCPServer")
    UDPSelf = TypeVar("UDPSelf", bound="UDPServer")
    ZMQSelf = TypeVar("ZMQSelf", bound="ZMQServer")
    PTYSelf = TypeVar("PTYSelf", bound="PTYServer")


IS_WINDOWS = sys.platform == "win32"


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

    def __init__(self, *, host: str = "127.0.0.1", port: int = 0, term: bytes | None = b"\n") -> None:
        """A TCP socket server.

        Args:
            host: The host to run the server on.
            port: The port number to use for the server.
            term: The termination character(s) to use for messages.
        """
        self.term: bytes | None = term
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

        def _start(term: bytes | None) -> None:
            self._conn, _ = self._sock.accept()
            while True:
                data = bytearray()
                while True:
                    try:
                        data.extend(self._conn.recv(4096))
                    except (ConnectionResetError, ConnectionAbortedError):
                        break

                    if not data or term is None or data.endswith(term):
                        break

                if not data or data.startswith(b"SHUTDOWN"):
                    break

                if data.startswith(b"CONTINUE"):
                    self._conn.sendall(b"NOT TERMINATED")
                    continue

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

        with contextlib.suppress(ConnectionError):
            self._conn.sendall(b"SHUTDOWN" + (self.term if self.term else b""))

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
        """Start a UDP server.

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
        self._context.set(zmq.BLOCKY, 0)
        self._socket: SyncSocket = self._context.socket(zmq.REP)

        self._host: str = host
        self._port: int = port
        if port == 0:
            self._port = self._socket.bind_to_random_port(f"tcp://{host}")
        else:
            _ = self._socket.bind(f"tcp://{host}:{port}")

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
                self._socket.send(data if self._queue.empty() else self._queue.get())
                if data == b"SHUTDOWN":
                    break

        self._thread = Thread(target=_start, daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return

        c = Connection(f"ZMQ::{self._host}::{self._port}")
        with c.connect() as dev:
            _ = dev.query(b"SHUTDOWN")

        self._thread.join()
        self._thread = None

        self._socket.unbind(f"tcp://{self._host}:{self._port}")
        self._context.destroy()
        self.clear_response_queue()


class PTYServer:
    """A serial server."""

    def __init__(self, *, term: bytes = b"\n") -> None:
        """A serial server.

        Args:
            term: The termination character(s) to use for messages.
        """
        import pty  # noqa: PLC0415

        self.term: bytes = term
        self._thread: Thread | None = None
        self._queue: Queue[bytes] = Queue()

        server, client = pty.openpty()  # type: ignore[attr-defined]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        self._server_fd: int = server
        self._client_fd: int = client
        self._name: str = os.ttyname(client)  # type: ignore[attr-defined]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    def __enter__(self: PTYSelf) -> PTYSelf:  # noqa: PYI019
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
    def name(self) -> str:
        """Returns the port name of the server."""
        return self._name

    def start(self, wait: float = 0.1) -> None:
        """Start a PTY server.

        Args:
            wait: The number of seconds to wait for the server to start before returning.
        """

        def _start(term: bytes) -> None:
            while True:
                data = bytearray()
                while not data.endswith(term):
                    data.extend(os.read(self._server_fd, 1))

                if data.startswith(b"SHUTDOWN"):
                    break

                msg = data if self._queue.empty() else self._queue.get()
                _ = os.write(self._server_fd, msg)

        self._thread = Thread(target=_start, args=(self.term,), daemon=True)
        self._thread.start()
        sleep(wait)

    def stop(self) -> None:
        """Stop the server and clear the response queue."""
        if self._thread is None:
            return

        _ = os.write(self._client_fd, b"SHUTDOWN" + self.term)

        self._thread.join()
        self._thread = None

        os.close(self._client_fd)
        os.close(self._server_fd)
        self.clear_response_queue()


class USBDeviceDescriptor:
    """Mocked USB Device Descriptor."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        vid: int = -1,
        pid: int = -1,
        serial: str = "",
        is_usb_tmc: bool = False,
        is_not_raw: bool = False,
        bus: int | None = 1,
        address: int | None = 1,
        alternate_setting: int = 0,
        num_configurations: int = 1,
        device_version: int = 0x1001,
        has_intr_read: bool = False,
    ) -> None:
        """Mocked USB Device Descriptor."""
        self.bLength: int = 18
        self.bDescriptorType: int = 0x01
        self.bcdUSB: int = 0x0200
        self.bDeviceClass: int = 0xFF
        self.bDeviceSubClass: int = 0xFF
        self.bDeviceProtocol: int = 0xFF
        self.bMaxPacketSize0: int = 64
        self.idVendor: int = vid
        self.idProduct: int = pid
        self.bcdDevice: int = device_version
        self.iManufacturer: int = 1
        self.iProduct: int = 2
        self.iSerialNumber: int = 3
        self.bNumConfigurations: int = num_configurations
        self.bus: int | None = bus
        self.address: int | None = address
        self.port_number: None = None
        self.port_numbers: None = None
        self.speed: None = None
        self.serial: str = serial

        self.is_usb_tmc: bool = is_usb_tmc
        self.is_not_raw: bool = is_not_raw
        self.alternate_setting: int = alternate_setting
        self.has_intr_read: bool = has_intr_read


class USBConfigurationDescriptor:
    """Mocked USB Configuration Descriptor."""

    def __init__(self) -> None:
        """Mocked USB Configuration Descriptor."""
        self.bLength: int = 9
        self.bDescriptorType: int = 2
        self.wTotalLength: int = 0x0020
        self.bNumInterfaces: int = 1
        self.bConfigurationValue: int = 1
        self.iConfiguration: int = 0
        self.bmAttributes: int = 0x80
        self.bMaxPower: int = 250
        self.extra_descriptors: list[int] = []


class USBInterfaceDescriptor:
    """Mocked USB Interface Descriptor."""

    def __init__(
        self, cls: int = 0xFF, sub_cls: int = 0xFF, alternate_setting: int = 0, num_endpoints: int = 2
    ) -> None:
        """Mocked USB Interface Descriptor."""
        self.bLength: int = 9
        self.bDescriptorType: int = 4
        self.bInterfaceNumber: int = 0
        self.bAlternateSetting: int = alternate_setting
        self.bNumEndpoints: int = num_endpoints
        self.bInterfaceClass: int = cls
        self.bInterfaceSubClass: int = sub_cls
        self.bInterfaceProtocol: int = 0xFF
        self.iInterface: int = 2
        self.extra_descriptors: list[int] = []


class USBEndpointDescriptor:
    """Mocked USB Endpoint Descriptor."""

    def __init__(self, ep_address: int, attributes: int) -> None:
        """Mocked USB Endpoint Descriptor."""
        self.bLength: int = 7
        self.bDescriptorType: int = 5
        self.bEndpointAddress: int = ep_address
        self.bmAttributes: int = attributes
        self.wMaxPacketSize: int = 0x0040
        self.bInterval: int = 0
        self.bRefresh: int = 0
        self.bSynchAddress: int = 0
        self.extra_descriptors: list[int] = []


class USBBackend(IBackend):  # type: ignore[misc, no-any-unimported] # pyright: ignore[reportUntypedBaseClass]
    """Mocked USB backend for testing the USB interface."""

    def __init__(self) -> None:
        """Mocked USB backend for testing the USB interface."""
        super().__init__()  # pyright: ignore[reportUnknownMemberType]
        self.read_offset: int = 0
        self._devices: list[USBDeviceDescriptor] = []
        self._device: USBDeviceDescriptor = USBDeviceDescriptor()
        self._bulk_message: array[int] = array("B")
        self._bulk_queue: Queue[bytes] = Queue()
        self._ctrl_queue: Queue[bytes] = Queue()
        self._intr_queue: Queue[bytes] = Queue()
        self._raise_bad_config_number: bool = False

    def add_bulk_response(self, content: bytes) -> None:
        """Add a bulk I/O response to the queue.

        Args:
            content: The content of the response message.
        """
        self._bulk_queue.put(content)

    def add_ctrl_response(self, content: bytes) -> None:
        """Add a control transfer response to the queue.

        Args:
            content: The content of the control transfer message.
        """
        self._ctrl_queue.put(content)

    def add_intr_response(self, content: bytes) -> None:
        """Add a interrupt response to the queue.

        Args:
            content: The content of the interrupt message.
        """
        self._intr_queue.put(content)

    def add_device(  # noqa: PLR0913
        self,
        vendor_id: int,
        product_id: int,
        serial: str,
        *,
        is_usb_tmc: bool = False,
        is_not_raw: bool = False,
        has_intr_read: bool = False,  # is_usb_tmc must also be true to use this properly
        alternate_setting: int = 0,
        bus: int | None = 1,
        address: int | None = 1,
        num_configurations: int = 1,
        device_version: int = 0x1001,
    ) -> None:
        """Add a device."""
        self._devices.append(
            USBDeviceDescriptor(
                vid=vendor_id,
                pid=product_id,
                serial=serial,
                is_usb_tmc=is_usb_tmc,
                is_not_raw=is_not_raw,
                alternate_setting=alternate_setting,
                bus=bus,
                address=address,
                num_configurations=num_configurations,
                device_version=device_version,
                has_intr_read=has_intr_read,
            )
        )

    def attach_kernel_driver(self, handle: int, interface: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def bulk_read(self, handle: int, ep: int, interface: int, buffer: array[int], timeout: int) -> int:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Mock a bulk read."""
        if self._bulk_queue.empty():
            # return data in wMaxPacketSize=64 chunks
            msg = self._bulk_message[self.read_offset : self.read_offset + 64]
            self.read_offset += 64
        else:
            msg = array("B", self._bulk_queue.get())

        if msg.tobytes() in {b"sleep", b"\x11\x60sleep"}:  # \x11\x60 are the status bytes for the FTDI packet
            sleep(0.05)

        buffer[:] = msg
        return len(msg)

    def bulk_write(self, handle: int, ep: int, interface: int, data: array[int], timeout: int) -> int:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Mock a bulk write."""
        self._bulk_message = data
        self.read_offset = 0
        as_bytes = data.tobytes()
        if as_bytes in {b"write_sleep!", b"sleep!"}:
            sleep(0.05)
            return len(data) // 2

        if as_bytes.endswith(b"\x00\x07\x00\x00\x00\x01\x00\x00\x00error\r\n\x00"):  # USBTMC message, after ~bTag
            error = "Mocked Bulk-OUT write error"
            raise usb.core.USBError(error)  # pyright: ignore[reportUnknownMemberType]

        return len(data)

    def claim_interface(self, handle: int, interface: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def clear_bulk_response_queue(self) -> None:
        """Clear the bulk I/O response queue."""
        with self._bulk_queue.mutex:
            self._bulk_queue.queue.clear()

    def clear_ctrl_response_queue(self) -> None:
        """Clear the control transfer I/O response queue."""
        with self._ctrl_queue.mutex:
            self._ctrl_queue.queue.clear()

    def clear_intr_response_queue(self) -> None:
        """Clear the interrupt response queue."""
        with self._intr_queue.mutex:
            self._intr_queue.queue.clear()

    def clear_halt(self, handle: int, ep: int) -> None:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Mock a clear-halt request."""
        if ep == 0x81:
            msg = "Mocked Bulk-IN clear-halt issue"
            raise usb.core.USBError(msg)  # pyright: ignore[reportUnknownMemberType]

    def close_device(self, handle: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def ctrl_transfer(
        self,
        handle: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        request_type: int,
        request: int,
        value: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        index: int,
        data: array[int],
        timeout: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
    ) -> int:
        """Return the number of bytes written (for OUT transfers) or to read (for IN transfers)."""
        if request_type == 1234:
            msg = "Transfer error"
            raise usb.core.USBError(msg)  # pyright: ignore[reportUnknownMemberType]

        if request_type == 9999:
            msg = "timeout"
            raise usb.core.USBTimeoutError(msg)  # pyright: ignore[reportUnknownMemberType]

        if request_type == 0xC0:  # FTDI control IN request
            buffer = self._ctrl_queue.get()
            data[: len(buffer)] = array("B", buffer)
            return len(buffer)

        if request_type == 0xA1 and request == 7:  # USBTMC GET_CAPABILITIES
            data[:] = array("B", [1, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0])
            return len(data)

        if request_type in {0xA1, 0xA2} and request in {1, 2, 3, 4, 5, 6, 64, 128, 160, 161, 162}:  # USBTMC
            buffer = self._ctrl_queue.get()
            data[: len(buffer)] = array("B", buffer)
            return len(buffer)

        if request == 0x06:  # get_descriptor()
            if index == 0:  # langid request
                data[:4] = array("B", [4, 3, 9, 4])  # langid = 1033
                return 4

            if index == 1033:
                serial = self._device.serial.encode("utf-16-le")
                n = len(serial) + 2
                data[:2] = array("B", [n, 3])
                data[2 : len(serial)] = array("B", serial)
                return n

        return len(data)

    def detach_kernel_driver(self, handle: int, interface: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def enumerate_devices(self) -> Iterator[USBDeviceDescriptor]:
        """Yield mocked devices. Also raises NoBackendError if there are no devices."""
        if not self._devices:
            msg = "No backend available"
            raise usb.core.NoBackendError(msg)  # pyright: ignore[reportUnknownMemberType]
        yield from self._devices

    def get_configuration(self, handle: int) -> int:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Receives the mocked handle."""
        if self._device.serial == "config-not-set":
            self._raise_bad_config_number = True
            return -1
        return USBConfigurationDescriptor().bConfigurationValue

    def get_configuration_descriptor(self, device: USBDeviceDescriptor, config: int) -> USBConfigurationDescriptor:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Return a mocked Configuration Descriptor."""
        if self._raise_bad_config_number:
            msg = "Mocked message from pyUSB"
            raise usb.core.USBError(msg)  # pyright: ignore[reportUnknownMemberType]
        return USBConfigurationDescriptor()

    def get_device_descriptor(self, device: USBDeviceDescriptor) -> USBDeviceDescriptor:
        """Returns the device descriptor."""
        self._device = device
        return device

    def get_endpoint_descriptor(
        self,
        device: USBDeviceDescriptor,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        ep: int,
        interface: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        alternate_settings: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        config: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
    ) -> USBEndpointDescriptor:
        """Return a mocked Endpoint Descriptor."""
        if ep == 0:
            ep_address, attributes = (0x81, 0x02)  # Bulk-IN
        elif ep == 1:
            ep_address, attributes = (0x02, 0x02)  # Bulk-OUT
        elif ep == 2:
            ep_address, attributes = (0x83, 0x03)  # Interrupt-IN
        else:
            msg = f"Mocked USBBackend: get_endpoint_descriptor() endpoint {ep} not handled"
            raise ValueError(msg)
        return USBEndpointDescriptor(ep_address, attributes)

    def get_interface_descriptor(
        self,
        device: USBDeviceDescriptor,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        interface: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        alternate_settings: int,
        config: int,  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
    ) -> USBInterfaceDescriptor:
        """Return a mocked Interface Descriptor."""
        if alternate_settings > 0:
            raise IndexError
        if self._device.is_usb_tmc:
            if self._device.has_intr_read:
                return USBInterfaceDescriptor(cls=0xFE, sub_cls=3, num_endpoints=3)
            return USBInterfaceDescriptor(cls=0xFE, sub_cls=3)
        if self._device.is_not_raw:
            return USBInterfaceDescriptor(cls=0x22, sub_cls=10)
        if self._device.alternate_setting != 0:
            return USBInterfaceDescriptor(alternate_setting=self._device.alternate_setting)
        return USBInterfaceDescriptor()

    def intr_read(self, handle: int, ep: int, interface: int, buffer: array[int], timeout: int) -> int:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Mock an interrupt read."""
        msg = array("B", self._intr_queue.get())
        buffer[: len(msg)] = msg
        return len(msg)

    def is_kernel_driver_active(self, handle: int, interface: int) -> bool:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """Raises NotImplementedError on Windows, otherwise returns True."""
        if IS_WINDOWS:
            raise NotImplementedError
        return True

    def open_device(self, device: USBDeviceDescriptor) -> int:
        """Returns a handle for the USB Device, 1."""
        self._device = device
        return 1

    def release_interface(self, handle: int, interface: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def reset_device(self, handle: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""

    def set_configuration(self, handle: int, config: int) -> None:  # pyright: ignore[reportUnusedParameter]
        """Does nothing."""


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


@pytest.fixture
def pty_server() -> type[PTYServer]:
    return PTYServer


@pytest.fixture
def usb_backend() -> USBBackend:
    return USBBackend()
