from __future__ import annotations

import sys
import threading
from array import array
from typing import TYPE_CHECKING

import numpy as np
import pytest
import zmq

from msl.equipment import Connection, Equipment, MSLConnectionError, ZeroMQ, ZeroMQServer
from msl.equipment.interfaces.zeromq import parse_zmq_address

if TYPE_CHECKING:
    from typing import Literal

    from conftest import ZMQServer
    from msl.equipment.typing import ZMQServerResponse


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


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = ZeroMQ(Equipment())


def test_multipart(zmq_server: type[ZMQServer]) -> None:  # noqa: PLR0915
    with zmq_server() as server:
        conn = Connection(f"ZMQ::{server.host}::{server.port}")
        dev: ZeroMQ
        with conn.connect() as dev:
            # the following test are primarily checks for when running type
            # checkers against the `ZMQMultiPart` definition

            t: Literal["u", "w"] = "u" if sys.version_info < (3, 13) else "w"
            out = dev.write_multipart([array(t, b"wwww")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"wwww"]

            out = dev.write_multipart([array("b", b"b")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"b"]

            out = dev.write_multipart([array("H", b"HH")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"HH"]

            out = dev.write_multipart([array("d", b"dddddddd")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"dddddddd"]

            out = dev.write_multipart([b"bytes"])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"bytes"]

            out = dev.write_multipart([bytearray(b"bytearray")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"bytearray"]

            out = dev.write_multipart([memoryview(b"memoryview")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"memoryview"]

            out = dev.write_multipart([zmq.Frame(b"frame")])
            assert out is None
            list_bytes = dev.read_multipart()
            assert list_bytes == [b"frame"]

            is_windows_and_python_3_8 = sys.platform == "win32" and sys.version_info < (3, 9)
            out = dev.write_multipart([np.array([1, 2])])
            assert out is None
            list_bytes = dev.read_multipart()
            if is_windows_and_python_3_8:
                assert list_bytes == [b"\x01\x00\x00\x00\x02\x00\x00\x00"]
            else:
                assert list_bytes == [b"\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00"]

            out = dev.write_multipart([np.array([1, 2], dtype="b")], copy=True)
            assert out is None
            list_bytes = dev.read_multipart(copy=True)
            assert list_bytes == [b"\x01\x02"]

            mt = dev.write_multipart([b"hello"], copy=False)
            assert isinstance(mt, zmq.MessageTracker)
            list_frame = dev.read_multipart(copy=False)
            assert len(list_frame) == 1
            assert isinstance(list_frame[0], zmq.Frame)
            assert list_frame[0].bytes == b"hello"


def test_zmq_server(capsys: pytest.CaptureFixture[str]) -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]  # noqa: PLR0911
            request = msg_parts[0]
            if request == b"empty":
                return b""
            if request == b"numpy":
                return np.array([1, 2], dtype=int)
            if request == b"array":
                return array("b", b"b")
            if request == b"frame":
                return zmq.Frame(b"frame")
            if request == b"bytes":
                return b"".join(msg_parts)
            if request == b"tuple":
                return (b"1", bytearray(b"2"), array("b", b"3"))
            return [b"a", bytearray(b"b"), array("b", b"c")]

        def shutdown_handler(self) -> None:  # pyright: ignore[reportImplicitOverride]
            _ = sys.stderr.write("foo")

    server = Server()
    assert server.address == "tcp://*"

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    while not server.port:
        pass

    client: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}").connect()
    assert client.write(b"empty") == 5
    assert client.read(decode=False) == b""

    reply = client.query(b"numpy", decode=False)
    assert np.array_equal(np.frombuffer(reply, dtype=int), [1, 2])

    assert client.query(b"array", decode=False) == b"b"
    assert client.query(b"frame", decode=False) == b"frame"
    assert client.query(b"bytes", decode=False) == b"bytes"

    assert client.write(b"tuple") == 5
    assert client.read_multipart() == [b"1", b"2", b"3"]

    # read() will only read a single ZMQ Frame
    assert client.write(b"else") == 4
    assert client.read(decode=False) == b"a"
    assert client.read(decode=False) == b"b"
    assert client.read(decode=False) == b"c"

    # read_multipart() will read all Frames
    assert client.write(b"else") == 4
    assert client.read_multipart() == [b"a", b"b", b"c"]

    assert server.address == f"tcp://0.0.0.0:{server.port}"

    server.shutdown_server()
    thread.join()

    out, err = capsys.readouterr()
    assert out.rstrip().endswith("Press Ctrl+C to shut down the server")
    assert err == "foo"


def test_zmq_server_port_and_no_display(capsys: pytest.CaptureFixture[str]) -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            return b"".join(msg_parts)

    port = 52817
    server = Server(port=port)
    assert server.address == "tcp://*:52817"

    thread = threading.Thread(target=server.start, daemon=True, kwargs={"info": False})
    thread.start()

    client: ZeroMQ = Connection(f"ZMQ::localhost::{port}").connect()
    assert client.write_multipart([b"h", b"i"]) is None
    assert client.read_multipart() == [b"hi"]

    assert server.address == "tcp://0.0.0.0:52817"

    server.shutdown_server()
    thread.join()

    out, err = capsys.readouterr()
    assert not out
    assert not err


def test_zmq_server_multipart_reply() -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            return msg_parts

    server = Server()

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    while not server.port:
        pass

    client: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}").connect()
    assert client.write_multipart([b"h", b"i"]) is None
    assert client.read_multipart() == [b"h", b"i"]

    server.shutdown_server()
    thread.join()


def test_zmq_server_zmq_pair() -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            if msg_parts[0] == b"skip":
                return None
            if msg_parts[0] == b"hello":
                return [b"world"]
            return b"bar"

    server = Server(socket_type="PAIR")

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    while not server.port:
        pass

    # Can write multiple messages without performing a read when using a zmq.PAIR
    client: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}", socket_type="PAIR").connect()
    assert client.query(b"foo", decode=False) == b"bar"
    assert client.write(b"skip") == 4
    assert client.query(b"foo", decode=False) == b"bar"
    assert client.write(b"skip") == 4
    assert client.write(b"hello") == 5
    assert client.read_multipart() == [b"world"]
    assert client.query("hello", decode=False) == b"world"
    assert client.query(b"foo", decode=False) == b"bar"

    # Another client cannot send a request
    client2: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}", socket_type="PAIR", timeout=0.1).connect()
    with pytest.raises(MSLConnectionError, match=r"Again: Resource temporarily unavailable"):
        _ = client2.query(b"foo", decode=False)

    server.shutdown_server()
    thread.join()


@pytest.mark.parametrize("allow", ["localhost", "127.0.0.1", ["10.20.30.40", "127.0.0.1"]])
def test_zmq_server_allow(allow: str | list[str]) -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            return msg_parts

    server = Server(allow=allow)

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    while not server.port:
        pass

    client: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}").connect()
    assert client.write(b"foo") == 3
    assert client.read_multipart() == [b"foo"]

    server.shutdown_server()
    thread.join()


def test_zmq_server_deny() -> None:

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            return msg_parts

    server = Server(allow="14.13.12.11")

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    while not server.port:
        pass

    client: ZeroMQ = Connection(f"ZMQ::localhost::{server.port}", timeout=0.1).connect()
    assert client.write(b"foo") == 3
    with pytest.raises(MSLConnectionError, match=r"Again: Resource temporarily unavailable"):
        _ = client.read()

    server.shutdown_server()
    thread.join()


@pytest.mark.filterwarnings("error")
def test_zmq_server_invalid_socket_type() -> None:
    # If ZeroMQServer.__del__ raises an error, this test hangs on Windows (maybe other OS'es)
    # If this test finishes that means there isn't an error when ZeroMQServer.__del__ is called

    class Server(ZeroMQServer):
        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:  # pyright: ignore[reportImplicitOverride]
            return msg_parts

    with pytest.raises(ValueError, match=r"Cannot create <enum 'SocketType'> from 'ABC'$"):
        _ = Server(socket_type="ABC")
