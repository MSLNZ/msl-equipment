# cSpell: ignore usbmodemHIDPC1 usbserial XGBL usbmodem
from __future__ import annotations

try:
    import pty
except ImportError:
    pty = None  # type: ignore[assignment]

from typing import TYPE_CHECKING

import pytest

from msl.equipment import Connection, Equipment, MSLConnectionError, MSLTimeoutError, Serial
from msl.equipment.interfaces.serial import _init_serial, parse_serial_address  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    from tests.conftest import PTYServer


@pytest.mark.parametrize(
    "address",
    [
        "",
        "ASRL",
        "COM",
        "LPT",
        "ASRLCOM",
        "XXXX4",
        "ABC2",
        "COMx",
        "GPIB0::2",
        "SDK::filename.so",
        "SOCKET::192.168.1.100::5000",
        "Prologix::COM6",
        "Prologix::COM3::6",
        "Prologix::ASRL3::6::112",
        "Prologix::ASRLCOM7::6::112",
        "Prologix::/dev/ttyS2::6",
        "PROLOGIX::/dev/ttyUSB1::1::96",
        "PROLOGIX::/dev/pts/1::2",
        "PROLOGIX::/dev/symlink_name::6",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_serial_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("COM1", "COM1"),
        ("ASRL2", "COM2"),
        ("ASRLCOM3", "COM3"),
        ("com11", "COM11"),
        ("asrl22", "COM22"),
        ("asrlcom10", "COM10"),
        ("COM12::INSTR", "COM12"),
        ("asrl2::instr", "COM2"),
        ("ASRLcom30::instr", "COM30"),
        ("COM/dev/ttyS0", "/dev/ttyS0"),
        ("ASRL/dev/ttyS1", "/dev/ttyS1"),
        ("ASRLCOM/dev/ttyS2", "/dev/ttyS2"),
        ("COM/dev/pts/12", "/dev/pts/12"),
        ("ASRL/dev/pts/12::INSTR", "/dev/pts/12"),
        ("ASRLCOM/dev/pts/1::INSTR", "/dev/pts/1"),
        ("COM/dev/ttyUSB0", "/dev/ttyUSB0"),
        ("COM/dev/ttyUSB10::INSTR", "/dev/ttyUSB10"),
        ("ASRL/dev/ttyUSB1", "/dev/ttyUSB1"),
        ("ASRL/dev/ttyUSB0::INSTR", "/dev/ttyUSB0"),
        ("COM/dev/symlink_name", "/dev/symlink_name"),
        ("ASRL/dev/symlink_name", "/dev/symlink_name"),
        ("ASRLCOM/dev/symlink_name", "/dev/symlink_name"),
        ("ASRLCOM/dev/ttyUSB2", "/dev/ttyUSB2"),
        ("ASRLCOM/dev/ttyUSB2::INSTR", "/dev/ttyUSB2"),
        ("ASRL/dev/cu.Bluetooth-Incoming-Port::INSTR", "/dev/cu.Bluetooth-Incoming-Port"),
        (
            "ASRL/dev/cu.usbmodemHIDPC1",
            "/dev/cu.usbmodemHIDPC1",
        ),
        ("ASRL/dev/cu.usbserial-FTE1XGBL::INSTR", "/dev/cu.usbserial-FTE1XGBL"),
        ("ASRL/dev/cu.usbmodem1421401::INSTR", "/dev/cu.usbmodem1421401"),
    ],
)
def test_parse_address_valid(address: str, expected: str) -> None:
    parsed = parse_serial_address(address)
    assert parsed is not None
    assert parsed.port == expected


@pytest.mark.skipif(pty is None, reason="pty is not available")
def test_session(pty_server: type[PTYServer]) -> None:
    term = b"\r\n"
    with pty_server(term=term) as server:
        c = Connection(
            f"ASRL{server.name}",
            termination=term,
            timeout=1,
            max_read_size=1 << 16,
        )

        dev: Serial = c.connect()
        assert dev.read_termination == term
        assert dev.write_termination == term

        assert dev.query("hello") == "hello\r\n"

        n = dev.write("hello")
        assert dev.read(size=n) == "hello\r\n"

        assert dev.write("x" * 4096) == 4096 + len(term)
        assert dev.read() == "x" * 4096 + term.decode()

        n = dev.write("123.456")
        with pytest.raises(MSLConnectionError, match=r"received 9 bytes, requested 10 bytes"):
            _ = dev.read(size=n + 1)

        with pytest.raises(MSLConnectionError, match=r"max_read_size is 65536 bytes, requesting 65537 bytes"):
            _ = dev.read(size=dev.max_read_size + 1)  # requesting more bytes than are maximally allowed

        dev.max_read_size = 10
        assert dev.write(b"a" * 999) == 999 + len(term)
        with pytest.raises(MSLConnectionError, match=r"RuntimeError: len\(message\) \[11\] > max_read_size \[10\]"):
            _ = dev.read()  # requesting more bytes than are maximally allowed

        dev.max_read_size = 1 << 16
        assert dev.read() == ("a" * (999 - 11)) + term.decode()  # clear the buffer

        msg = "a" * (dev.max_read_size - len(term))
        assert dev.write(msg) == dev.max_read_size
        assert dev.read() == msg + term.decode()

        assert dev.write(b"021.3" + term + b",054.2") == 15
        assert dev.read() == "021.3\r\n"  # read until first `term`
        assert dev.read() == ",054.2\r\n"  # read until second `term`

        assert dev.write(b"021.3" + term + b",054.2" + term) == 15
        assert dev.read(size=1) == "0"
        assert dev.read(size=3) == "21."
        assert dev.read(size=2) == "3\r"
        assert dev.read(size=2) == "\n,"
        assert dev.read(size=1) == "0"
        assert dev.read(size=1) == "5"
        assert dev.read(size=1) == "4"
        assert dev.read() == ".2\r\n"

        dev.disconnect()


@pytest.mark.skipif(pty is None, reason="pty is not available")
def test_timeout(pty_server: type[PTYServer]) -> None:
    term = b"\n"
    with pty_server(term=term) as server:
        c = Connection(
            f"ASRL{server.name}",
            termination=term,
            timeout=21,
        )

        dev: Serial = c.connect()

        assert dev.timeout == 21
        assert dev.serial.timeout == 21
        assert dev.serial.write_timeout == 21

        dev.timeout = None
        assert dev.timeout is None
        assert dev.serial.timeout is None
        assert dev.serial.write_timeout is None  # type: ignore[unreachable]

        dev.timeout = 10
        assert dev.timeout == 10
        assert dev.serial.timeout == 10
        assert dev.serial.write_timeout == 10

        dev.timeout = -1
        assert dev.timeout is None
        assert dev.serial.timeout is None
        assert dev.serial.write_timeout is None

        dev.timeout = 0.1
        assert dev.timeout == 0.1
        assert dev.serial.timeout == 0.1
        assert dev.serial.write_timeout == 0.1

        with pytest.raises(MSLTimeoutError):
            _ = dev.read()

        dev.disconnect()


@pytest.mark.skipif(pty is None, reason="pty is not available")
def test_logging(pty_server: type[PTYServer], caplog: pytest.LogCaptureFixture) -> None:
    term = b"\n"
    server = pty_server(term=term)
    server.start()

    timeout = 0.1
    address = f"ASRL{server.name}"
    connection = Connection(
        address,
        termination=term,
        timeout=timeout,
    )

    caplog.set_level("DEBUG", "msl.equipment")
    caplog.clear()

    dev: Serial = connection.connect()
    dev.rstrip = True
    assert dev.query("foo", delay=timeout * 2) == "foo"  # delay doesn't impact timeout
    dev.disconnect()
    dev.disconnect()  # multiple times is ok and only logs "Disconnected from ..." once
    dev.disconnect()
    assert caplog.messages == [
        f"Connecting to Serial<|| at {address}>",
        "Serial<||>.write(b'foo\\n')",
        "Serial<||>.read() -> b'foo\\n'",
        f"Disconnected from Serial<|| at {address}>",
    ]

    server.stop()


@pytest.mark.skipif(pty is None, reason="pty is not available")
@pytest.mark.parametrize("term", [b"\r", b"\n", b"\0", b"\r\n", b"\n\0", b"\r\0", b"\r\n\0", b"anything"])
def test_terminator(term: bytes, pty_server: type[PTYServer]) -> None:
    with pty_server(term=term) as server:
        c = Connection(f"ASRL{server.name}", termination=term)
        with c.connect() as dev:
            assert dev.read_termination == term
            assert dev.write_termination == term
            assert dev.query("hello", decode=False) == b"hello" + term


def test_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid serial address 'bad'"):
        _ = Serial(Equipment(connection=Connection("bad")))


def test_invalid_port() -> None:
    with pytest.raises(MSLConnectionError, match=r"could not open port"):
        _ = Serial(Equipment(connection=Connection("COM254")))


def test_init_serial_defaults() -> None:
    s = _init_serial("A", {})
    assert s.baudrate == 9600
    assert s.dsrdtr is False
    assert s.inter_byte_timeout is None
    assert s.parity == "N"
    assert s.port == "A"
    assert s.rtscts is False
    assert s.stopbits == 1
    assert s.xonxoff is False


@pytest.mark.parametrize("properties", [{"baud_rate": 115200}, {"baudrate": 115200}])
def test_init_serial_baudrate(properties: dict[str, int]) -> None:
    s = _init_serial("A", properties)
    assert s.baudrate == 115200


@pytest.mark.parametrize("properties", [{"data_bits": 6}, {"data_bits": "six"}, {"bytesize": 6}, {"bytesize": "six"}])
def test_init_serial_data_bits(properties: dict[str, int | str]) -> None:
    s = _init_serial("A", properties)
    assert s.bytesize == 6


@pytest.mark.parametrize("properties", [{"dsr_dtr": True}, {"dsrdtr": True}])
def test_init_serial_dsr_dtr(properties: dict[str, bool]) -> None:
    s = _init_serial("A", properties)
    assert s.dsrdtr is True


def test_init_serial_inter_byte_timeout() -> None:
    s = _init_serial("A", {"inter_byte_timeout": 5.2})
    assert s.inter_byte_timeout == 5.2


@pytest.mark.parametrize("properties", [{"parity": "even"}, {"parity": "E"}])
def test_init_serial_parity(properties: dict[str, str]) -> None:
    s = _init_serial("A", properties)
    assert s.parity == "E"


@pytest.mark.parametrize("properties", [{"rts_cts": True}, {"rtscts": True}])
def test_init_serial_rts_cts(properties: dict[str, bool]) -> None:
    s = _init_serial("A", properties)
    assert s.rtscts is True


@pytest.mark.parametrize("properties", [{"stop_bits": 2}, {"stop_bits": "two"}, {"stopbits": 2}, {"stopbits": "two"}])
def test_init_serial_stop_bits(properties: dict[str, int | str]) -> None:
    s = _init_serial("A", properties)
    assert s.stopbits == 2


@pytest.mark.parametrize("properties", [{"xon_xoff": True}, {"xonxoff": True}])
def test_init_serial_xon_xoff(properties: dict[str, bool]) -> None:
    s = _init_serial("A", properties)
    assert s.xonxoff is True


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = Serial(Equipment())
