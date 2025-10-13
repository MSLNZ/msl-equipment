from __future__ import annotations

import math
import os
from typing import TYPE_CHECKING

import pytest
from pyvisa.attributes import AttrVI_ATTR_TMO_VALUE
from pyvisa.resources.tcpip import TCPIPSocket

from msl.equipment import Backend, Connection, Equipment, Parity, PyVISA, StopBits
from msl.equipment.interfaces.pyvisa import _prepare_kwargs  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    from tests.conftest import TCPServer


def teardown_module() -> None:
    _ = os.environ.pop("PYVISA_LIBRARY", "")


def setup_module() -> None:
    os.environ["PYVISA_LIBRARY"] = "@py"


@pytest.mark.parametrize("parity", ["even", "EVEN", "E", 2, Parity.EVEN])
def test_prepare_kwargs_parity(parity: str | int) -> None:
    # even parity in pyvisa has enum value 2
    assert _prepare_kwargs({"parity": parity}) == {"parity": 2}


@pytest.mark.parametrize("stop_bits", ["one_point_five", "ONE_POINT_FIVE", 1.5, 15, StopBits.ONE_POINT_FIVE])
def test_prepare_kwargs_stop_bits(stop_bits: str | int) -> None:
    # one_and_a_half stop_bits in pyvisa has enum value 15
    assert _prepare_kwargs({"stop_bits": stop_bits}) == {"stop_bits": 15}


@pytest.mark.parametrize(
    ("term", "expected"), [("\r", "\r"), (b"\r", "\r"), ("\r\n", "\r\n"), (b"\r\n", "\r\n"), (b"abcdefg", "abcdefg")]
)
def test_prepare_kwargs_termination(term: str | bytes, expected: str) -> None:
    assert _prepare_kwargs({"termination": term}) == {"read_termination": expected, "write_termination": expected}


@pytest.mark.parametrize(
    ("term", "expected"), [("\r", "\r"), (b"\r", "\r"), ("\r\n", "\r\n"), (b"\r\n", "\r\n"), (b"abcdefg", "abcdefg")]
)
def test_prepare_kwargs_read_termination(term: str | bytes, expected: str) -> None:
    assert _prepare_kwargs({"read_termination": term}) == {"read_termination": expected}


@pytest.mark.parametrize(
    ("term", "expected"), [("\r", "\r"), (b"\r", "\r"), ("\r\n", "\r\n"), (b"\r\n", "\r\n"), (b"abcdefg", "abcdefg")]
)
def test_prepare_kwargs_write_termination(term: str | bytes, expected: str) -> None:
    assert _prepare_kwargs({"write_termination": term}) == {"write_termination": expected}


@pytest.mark.parametrize(
    ("timeout", "expected"),
    [
        (-1.5, 0),
        (0, 0),
        (10, 10000),
        (599, 599000),
        (600, 600),
        (5000, 5000),
        (None, None),
        (float("+inf"), float("+inf")),
    ],
)
def test_prepare_kwargs_timeout(timeout: float | None, expected: float | None) -> None:
    assert _prepare_kwargs({"timeout": timeout}) == {"timeout": expected}


def test_timeout_and_termination_query(tcp_server: type[TCPServer]) -> None:
    term = b"abc"
    server = tcp_server(term=term)
    server.start()

    os.environ["PYVISA_LIBRARY"] = "@py"

    address = f"TCPIP::{server.host}::{server.port}::SOCKET"
    conn = Connection(
        address,
        manufacturer="A",
        model="B",
        serial="C",
        backend=Backend.PyVISA,
        termination=term,
        timeout=10,
    )

    dev = conn.connect()
    assert str(dev) == "PyVISA<A|B|C>"
    assert repr(dev) == f"PyVISA<A|B|C at {address}>"

    assert dev.timeout == 10000  # 10 seconds gets converted to 10000 ms
    assert dev.write_termination == term.decode()
    assert dev.read_termination == term.decode()

    dev.timeout = 1234
    dev.write_termination = "hello"
    dev.read_termination = "goodbye"
    assert dev.timeout == 1234
    assert dev.write_termination == "hello"
    assert dev.read_termination == "goodbye"

    del dev.timeout
    dev.write_termination = None
    dev.read_termination = None
    assert math.isinf(dev.timeout)
    assert dev.write_termination is None
    assert dev.read_termination is None

    dev.timeout = 5000
    dev.write_termination = term.decode()
    dev.read_termination = term.decode()
    assert dev.timeout == 5000
    assert dev.write_termination == term.decode()
    assert dev.read_termination == term.decode()

    dev.timeout = None
    assert math.isinf(dev.timeout)  # pyright: ignore[reportArgumentType]

    assert dev.query("*IDN?") == "*IDN?"

    dev.write("foo")
    assert dev.read() == "foo"

    dev.disconnect()
    server.stop()


def test_timeout_and_termination_1(tcp_server: type[TCPServer]) -> None:
    term = b"abc"
    server = tcp_server(term=term)
    server.start()

    conn = Connection(
        f"TCPIP::{server.host}::{server.port}::SOCKET",
        backend="PyVISA",
        write_termination=b"abc",
        read_termination="123",
        timeout=1000,
    )

    dev = conn.connect()
    assert dev.timeout == 1000  # >600 so does not get converted
    assert dev.write_termination == "abc"
    assert dev.read_termination == "123"

    dev.disconnect()
    server.stop()


def test_timeout_and_termination_2(tcp_server: type[TCPServer]) -> None:
    term = b"abc"
    server = tcp_server(term=term)
    server.start()

    conn = Connection(
        f"TCPIP::{server.host}::{server.port}::SOCKET",
        backend="PyVISA",
    )

    dev = conn.connect()
    assert dev.timeout == AttrVI_ATTR_TMO_VALUE.default
    assert dev.write_termination == TCPIPSocket._write_termination  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.read_termination == TCPIPSocket._read_termination  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.read_termination is None

    dev.disconnect()
    server.stop()


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = PyVISA(Equipment())
