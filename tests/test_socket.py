from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

from msl.equipment import Connection, Equipment, MSLConnectionError, MSLTimeoutError, Socket
from msl.equipment.interfaces.socket import parse_socket_address

if TYPE_CHECKING:
    from tests.conftest import TCPServer, UDPServer


def test_tcp_socket_read(tcp_server: type[TCPServer]) -> None:  # noqa: PLR0915
    term = b"\r\n"
    server = tcp_server(term=term)
    server.start()

    connection = Connection(
        address=f"TCP::{server.host}::{server.port}",
        timeout=1,
        termination=term,
    )

    dev: Socket = connection.connect()

    assert dev.read_termination == term
    assert dev.write_termination == term

    assert dev.write("hello") == 5 + len(term)
    assert dev.read() == "hello\r\n"

    n = dev.write("hello")
    assert n == 5 + len(term)
    assert dev.read(size=n) == "hello\r\n"

    n = dev.write(b"021.3" + term + b",054.2")
    assert n == 5 + len(term) + 6 + len(term)
    assert dev.read(size=n) == "021.3\r\n,054.2\r\n"

    assert dev.write(b"021.3" + term + b",054.2") == 15
    assert dev.read(size=3) == "021"
    assert dev.read(size=5) == ".3\r\n,"
    assert dev.read() == "054.2\r\n"

    assert dev.write(b"021.3" + term + b",054.2") == 15
    assert dev.read() == "021.3\r\n"
    assert dev.read() == ",054.2\r\n"

    assert dev.write(b"021.3" + term + b",054.2" + term) == 15
    assert dev.read(size=1) == "0"
    assert dev.read(size=3) == "21."
    assert dev.read(size=2) == "3\r"
    assert dev.read(size=2) == "\n,"
    assert dev.read(size=1) == "0"
    assert dev.read(size=1) == "5"
    assert dev.read(size=1) == "4"
    assert dev.read() == ".2\r\n"

    n = dev.write("12345")
    assert n == 7
    with pytest.raises(MSLTimeoutError):
        _ = dev.read(size=n + 1)  # read more bytes than are available
    assert dev.read(size=n) == "12345\r\n"
    assert len(dev._byte_buffer) == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    msg = "a" * (dev.max_read_size - len(term))
    assert dev.write(msg) == dev.max_read_size
    assert dev.read() == msg + term.decode()

    assert dev.write(b"x" * 1024 + term + b"y" * 2048) == 1024 + 2048 + (len(term) * 2)
    assert dev.read() == "x" * 1024 + term.decode()  # read until `term`
    assert len(dev._byte_buffer) == 2048 + len(term)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    dev.max_read_size = 2000
    with pytest.raises(MSLConnectionError, match=r"max_read_size is 2000 bytes, requesting 2048 bytes"):
        _ = dev.read(size=2048)  # requesting more bytes than are maximally allowed
    dev.max_read_size = 3000  # allow for reading the buffer to clear it
    assert dev.read() == "y" * 2048 + term.decode()

    dev.max_read_size = 10
    assert dev.write(b"a" * 999) == 999 + len(term)
    with pytest.raises(MSLConnectionError, match=r"RuntimeError: len\(message\) \[1001\] > max_read_size \[10\]"):
        _ = dev.read()  # requesting more bytes than are maximally allowed
    dev.max_read_size = 1 << 16
    assert dev.read() == ("a" * 999) + term.decode()  # clear the buffer

    dev.rstrip = True
    assert dev.write(b"abc" + term + b"def ghi j   " + term) == 19
    assert dev.read() == "abc"
    assert dev.read() == "def ghi j"

    dev.rstrip = False  # the termination characters are okay for fmt = ieee, hp, ascii

    _ = dev.write(b"header", data=range(10), fmt="ieee", dtype="<f")
    reply = dev.read(fmt="ieee", dtype="<f")
    assert np.array_equal(reply, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

    _ = dev.write(b"header, ", data=range(5), fmt="hp", dtype=int)
    reply = dev.read(fmt="hp", dtype=int)
    assert np.array_equal(reply, [0, 1, 2, 3, 4])

    _ = dev.write(b"", data=(-49, 1000, -5821, 0), fmt="ascii", dtype="d")
    reply = dev.read(fmt="ascii", dtype=int)
    assert np.array_equal(reply, [-49, 1000, -5821, 0])

    _ = dev.write(b"", data=[1.23], fmt="ascii", dtype=".4e")
    reply = dev.read(fmt="ascii", dtype=float)
    assert reply.shape == (1,)
    assert reply.size == 1
    assert np.array_equal(reply, [1.23])

    dev.rstrip = True  # important, otherwise the read buffer has 2 extra bytes for fmt = None

    _ = dev.write(b"", data=(-1.53, 2.34, 9.72, 3.46), fmt=None, dtype=">f")
    reply = dev.read(fmt=None, dtype=">f")
    assert np.array_equal(reply, np.array([-1.53, 2.34, 9.72, 3.46], dtype=">f"))

    assert dev.query("message", decode=True) == "message"
    assert dev.query("message", decode=False) == b"message"

    dev.disconnect()
    server.stop()


def test_tcp_socket_timeout(tcp_server: type[TCPServer]) -> None:
    write_termination = b"\n"
    server = tcp_server(term=write_termination)
    server.start()

    connection = Connection(
        address=f"TCPIP::{server.host}::{server.port}::SOCKET",
        write_termination=write_termination,
        timeout=7,
    )

    dev: Socket = connection.connect()
    assert dev.socket is not None

    assert dev.timeout == 7
    assert dev.socket.gettimeout() == 7.0

    dev.timeout = None
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = 0.1
    assert dev.timeout == 0.1
    assert dev.socket.gettimeout() == 0.1

    dev.timeout = 0
    assert dev.timeout == 0
    assert dev.socket.gettimeout() == 0

    dev.timeout = -1
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None  # type: ignore[unreachable]

    dev.timeout = -12345
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = 10
    assert dev.timeout == 10
    assert dev.socket.gettimeout() == 10

    dev.timeout = 1e-6
    with pytest.raises(MSLTimeoutError):
        _ = dev.query(b"CONTINUE")

    dev.disconnect()
    server.stop()


def test_udp_socket_read(udp_server: type[UDPServer]) -> None:
    term = b"^END"
    server = udp_server(term=term)
    server.start()

    connection = Connection(
        address=f"UDP::{server.host}::{server.port}",
        termination=term,
        timeout=0.5,
    )

    dev: Socket = connection.connect()

    assert dev.read_termination == term
    assert dev.write_termination == term

    assert dev.write("hello") == 5 + len(term)
    assert dev.read() == "hello^END"

    n = dev.write("hello")
    assert n == 9
    assert dev.read(size=n) == "hello^END"

    n = dev.write(b"021.3" + term + b",054.2")
    assert dev.read(size=n) == "021.3^END,054.2^END"

    assert dev.write(b"021.3" + term + b",054.2") == 5 + len(term) + 6 + len(term)
    assert dev.read(size=3) == "021"
    assert dev.read(size=5) == ".3^EN"
    assert dev.read() == "D,054.2^END"

    assert dev.write(b"021.3" + term + b",054.2") == 5 + len(term) + 6 + len(term)
    assert dev.read() == "021.3^END"
    assert dev.read() == ",054.2^END"

    n = dev.write("12345")
    assert n == 9
    with pytest.raises(MSLTimeoutError):
        _ = dev.read(size=n + 1)  # read more bytes than are available
    assert dev.read(size=n) == "12345^END"  # still in buffer
    assert len(dev._byte_buffer) == 0  # buffer empty  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    dev.disconnect()
    server.stop()


def test_tcp_for_udp_server(udp_server: type[UDPServer]) -> None:
    with udp_server() as server:
        connection = Connection(
            address=f"TCP::{server.host}::{server.port}",  # using TCP for a UDP server
            timeout=0.2,
        )

        error = MSLTimeoutError if sys.platform == "win32" else MSLConnectionError
        with pytest.raises(error):
            _ = connection.connect()


def test_udp_for_tcp_server(tcp_server: type[TCPServer]) -> None:
    with tcp_server() as server:
        connection = Connection(
            address=f"UDP::{server.host}::{server.port}",  # using UDP for a TCP server
            timeout=0.2,
        )

        dev = connection.connect()
        error = MSLConnectionError if sys.platform == "win32" else MSLTimeoutError
        with pytest.raises(error):
            _ = dev.query("Hi")


@pytest.mark.parametrize(
    ("address", "host", "port"),
    [
        ("TCP::1.2.3.4::1234", "1.2.3.4", 1234),
        ("UDP::192.168.87.110::1234", "192.168.87.110", 1234),
        ("TCP::can-be-anything-without-spaces::60218", "can-be-anything-without-spaces", 60218),
        ("UDP::192.168.87.110::1234::some::extra::stuff::added", "192.168.87.110", 1234),
        ("TCPIP::dev.company.org::318::SOCKET", "dev.company.org", 318),
        ("TCPIP0::dev.company.org::318::SOCKET", "dev.company.org", 318),
        ("TCPIP10::dev.company.org::318::SOCKET", "dev.company.org", 318),
    ],
)
def test_parse_address(address: str, host: str, port: int) -> None:
    parsed = parse_socket_address(address)
    assert parsed is not None
    assert parsed == (host, port)


@pytest.mark.parametrize(
    "address",
    [
        "",
        "TCP",
        "TCP::",
        "TCP::1.2.3.4",
        "TCP::1.2.3.4::",
        "TCP::1.2.3.4::port",
        "COM5",
        "ASRL::COM11::INSTR",
        "GPIB::11",
        "Prologix::1.2.3.4::1234",
        "TCPIP::dev.company.org::318",
        "TCPIP::full.domain.name::1234::INVALID",
        "TCPIP::192.168.1.100::1234::INSTR",
        "TCPIP::1.2.3.4::hislip0::INSTR",
        "TCPIP::dev.company.com::INSTR",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    parsed = parse_socket_address(address)
    assert parsed is None

    with pytest.raises(ValueError, match="Invalid socket address"):
        _ = Socket(Equipment(connection=Connection(address)))


@pytest.mark.parametrize("term", [b"\r", b"\n", b"\0", b"\r\n", b"\n\0", b"\r\0", b"\r\n\0", b"anything"])
def test_terminator(tcp_server: type[TCPServer], term: bytes) -> None:
    with tcp_server(term=term) as server:
        connection = Connection(
            address=f"TCP::{server.host}::{server.port}",
            termination=term,
            timeout=0.2,
        )
        with connection.connect() as dev:
            assert dev.read_termination == term
            assert dev.write_termination == term
            assert dev.query("hello") == f"hello{term.decode()}"


def test_logging_messages(udp_server: type[UDPServer], caplog: pytest.LogCaptureFixture) -> None:
    term = b"X"
    with udp_server(term=term) as server:
        address = f"UDP::{server.host}::{server.port}"
        c = Connection(address, termination=term, timeout=0.2)
        with caplog.at_level("DEBUG"):
            dev: Socket = c.connect()
            assert dev.query("hello") == "helloX"
            assert dev.query("hello", size=2) == "he"
            assert dev.read() == "lloX"

            _ = dev.write(b"", data=[4, 3, 2], fmt="ieee", dtype="H")
            reply = dev.read(fmt="ieee", dtype="H")
            assert np.array_equal(reply, [4, 3, 2])

            dev.disconnect()
            dev.disconnect()  # multiple times is ok and only logs "Disconnected from ..." once
            dev.disconnect()
            assert caplog.messages == [
                f"Connecting to Socket<|| at {address}>",
                "Socket<||>.write(b'helloX')",
                "Socket<||>.read() -> b'helloX'",
                "Socket<||>.write(b'helloX')",
                "Socket<||>.read(size=2) -> b'he'",
                "Socket<||>.read() -> b'lloX'",
                "Socket<||>.write(b'#16\\x04\\x00\\x03\\x00\\x02\\x00X')",
                "Socket<||>.read(dtype='H', fmt='ieee') -> b'#16\\x04\\x00\\x03\\x00\\x02\\x00X'",
                f"Disconnected from Socket<|| at {address}>",
            ]


def test_empty_termination(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"") as server:
        connection = Connection(
            address=f"TCP::{server.host}::{server.port}",
            termination=b"",
            timeout=0.2,
        )
        with connection.connect() as dev:
            assert dev.read_termination == b""
            assert dev.write_termination == b""
            assert dev.query("hello", size=5, decode=False) == b"hello"


def test_reconnect_udp(udp_server: type[UDPServer]) -> None:
    term = b"\r\n"
    server = udp_server(term=term)
    server.start()

    port = server.port

    connection = Connection(
        address=f"UDP::{server.host}::{port}",
        termination=term,
        timeout=0.2,
    )

    dev: Socket = connection.connect()
    dev.rstrip = True
    assert dev.query("foo") == "foo"
    assert dev.write(b"SHUTDOWN") == 10

    server.stop()

    error = MSLConnectionError if sys.platform == "win32" else MSLTimeoutError
    with pytest.raises(error):
        _ = dev.query("foo")

    server = udp_server(port=port, term=term)
    server.start()

    dev.reconnect()
    assert dev.query("foo") == "foo"
    dev.disconnect()

    server.stop()


def test_reconnect_tcp(tcp_server: type[TCPServer], caplog: pytest.LogCaptureFixture) -> None:
    term = b"\r\n"
    server = tcp_server(term=term)
    server.start()

    host, port = server.host, server.port
    address = f"TCP::{host}::{port}"
    connection = Connection(
        address,
        termination=term,
        timeout=0.1,
    )

    dev: Socket = connection.connect()
    dev.rstrip = True
    assert dev.query("foo") == "foo"

    assert dev.write(b"SHUTDOWN") == 8 + len(term)

    server.stop()

    with pytest.raises(MSLConnectionError):
        _ = dev.query("foo")

    with caplog.at_level("DEBUG"):
        with pytest.raises(MSLConnectionError):
            dev.reconnect(max_attempts=5)

        messages = caplog.messages
        assert len(messages) == 6
        assert messages[0].startswith(f"Socket<|| at {address}> ConnectionAbortedError")
        assert messages[1].rstrip() == f"Socket<|| at {address}> Timeout occurred after 0.1 second(s)."
        assert messages[2].startswith(f"Socket<|| at {address}> Cannot connect to {host}:{port}")
        assert messages[3].startswith(f"Socket<|| at {address}> Cannot connect to {host}:{port}")
        assert messages[4].startswith(f"Socket<|| at {address}> Cannot connect to {host}:{port}")
        assert messages[5].startswith(f"Socket<|| at {address}> Cannot connect to {host}:{port}")

    server = tcp_server(port=port, term=term)
    server.start()

    dev.reconnect()
    assert dev.query("foo") == "foo"
    dev.disconnect()

    server.stop()
