from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import zmq

from msl.equipment import Connection, Equipment, MSLConnectionError
from msl.equipment.interfaces.zeromq import ZeroMQ, parse_zmq_address

if TYPE_CHECKING:
    from tests.conftest import ZMQServer


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("ZMQ::1.2.3.4::5555", ("1.2.3.4", 5555)),
        ("zmq::company::12345", ("company", 12345)),
        ("ZmQ::dev.company.org::111", ("dev.company.org", 111)),
    ],
)
def test_parse_address_valid(address: str, expected: tuple[str, int]) -> None:
    info = parse_zmq_address(address)
    assert info is not None

    host, port = expected
    assert info.host == host
    assert info.port == port


@pytest.mark.parametrize(
    "address",
    [
        "TCPIP::dev.company.com::INSTR",
        "GPIB::23",
        "SOCKET::myMachine::1234",
        "TCP::127.0.0.1::5555",
        "ZMQ::127.0.0.1::port",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_zmq_address(address) is None


def test_connect_address_invalid() -> None:
    equipment = Equipment(connection=Connection("ZMQ::127.0.0.1"))
    with pytest.raises(ValueError, match=r"Invalid ZeroMQ address"):
        _ = ZeroMQ(equipment)


def test_no_server() -> None:
    # ZeroMQ does not verify the server is running until a write/read
    conn = Connection("ZMQ::127.0.0.1::53182", timeout=0.1)
    zmq = conn.connect()
    with pytest.raises(MSLConnectionError, match=r"Resource temporarily unavailable"):
        _ = zmq.query("hi")


def test_socket_type_invalid() -> None:
    conn = Connection("ZMQ::127.0.0.1::46283", socket_type=99999)
    with pytest.raises(ValueError, match=r"Cannot create <enum 'SocketType'> from 99999"):
        conn.connect()


def test_protocol_invalid() -> None:
    conn = Connection("ZMQ::127.0.0.1::58244", protocol="invalid")
    with pytest.raises(MSLConnectionError, match=r"Protocol not supported"):
        conn.connect()


def test_query(zmq_server: type[ZMQServer]) -> None:
    server = zmq_server()
    server.start()

    conn = Connection(f"ZMQ::{server.host}::{server.port}", read_termination="ignored")
    dev: ZeroMQ = conn.connect()
    assert dev.read_termination is None
    assert dev.write_termination is None

    dev.max_read_size = 32  # the _socket attribute must exist for _set_interface_max_read_size
    assert dev.max_read_size == 32

    dev.timeout = 0.5  # the _socket attribute must exist for _set_interface_timeout
    assert dev.timeout == 0.5

    assert dev.query("hello") == "hello"
    assert dev.query("world", decode=False) == b"world"
    assert dev.query("123456789", size=4) == "1234"

    assert dev.write(b"foo")
    assert dev.read() == "foo"

    dev.disconnect()
    dev.disconnect()  # multiple times is ok
    dev.disconnect()
    server.stop()


def test_multiple_context(zmq_server: type[ZMQServer]) -> None:
    server = zmq_server()
    server.start()

    c1 = Connection(f"ZMQ::{server.host}::{server.port}")
    z1: ZeroMQ = c1.connect()

    c2 = Connection(f"ZMQ::{server.host}::{server.port}")
    z2: ZeroMQ = c2.connect()

    server.add_response(b"bar")
    server.add_response(b"baz")

    assert z1.query("foo") == "bar"
    assert z2.query("foo") == "baz"

    z1.disconnect()

    assert z2.query("echo") == "echo"
    z2.disconnect()

    server.stop()


def test_logging_messages(zmq_server: type[ZMQServer], caplog: pytest.LogCaptureFixture) -> None:
    with zmq_server() as server:
        address = f"ZMQ::{server.host}::{server.port}"
        c = Connection(address)

        caplog.set_level("DEBUG", "msl.equipment")
        caplog.clear()

        zmq: ZeroMQ = c.connect()
        assert zmq.query("hello") == "hello"
        assert zmq.query("hello", size=2) == "he"
        zmq.disconnect()
        zmq.disconnect()  # multiple times is ok and only logs "Disconnected from ..." once
        zmq.disconnect()
        assert caplog.messages == [
            f"Connecting to ZeroMQ<|| at {address}>",
            "ZeroMQ<||>.write(b'hello')",
            "ZeroMQ<||>.read() -> b'hello'",
            "ZeroMQ<||>.write(b'hello')",
            "ZeroMQ<||>.read(size=2) -> b'he'",
            f"Disconnected from ZeroMQ<|| at {address}>",
        ]


def test_set_interface(zmq_server: type[ZMQServer]) -> None:
    with zmq_server() as server:
        conn = Connection(f"ZMQ::{server.host}::{server.port}", termination="X")
        with conn.connect() as dev:
            assert dev.read_termination is None
            assert dev.write_termination is None

            dev.max_read_size = 32
            assert dev.max_read_size == 32
            assert dev.socket.getsockopt(zmq.MAXMSGSIZE) == 32

            dev.timeout = 0.5
            assert dev.timeout == 0.5
            assert dev.socket.getsockopt(zmq.RCVTIMEO) == 500
            assert dev.socket.getsockopt(zmq.SNDTIMEO) == 500

            dev.timeout = -1
            assert dev.timeout is None
            assert dev.socket.getsockopt(zmq.RCVTIMEO) == -1
            assert dev.socket.getsockopt(zmq.SNDTIMEO) == -1

            dev.timeout = 10
            assert dev.timeout == 10
            assert dev.socket.getsockopt(zmq.RCVTIMEO) == 10_000
            assert dev.socket.getsockopt(zmq.SNDTIMEO) == 10_000

            dev.timeout = None
            assert dev.timeout is None
            assert dev.socket.getsockopt(zmq.RCVTIMEO) == -1
            assert dev.socket.getsockopt(zmq.SNDTIMEO) == -1
