# cSpell: ignore usbmodemHIDPC1 usbserial XGBL usbmodem
from __future__ import annotations

try:
    import pty
except ImportError:
    pty = None  # type: ignore[assignment]

from typing import TYPE_CHECKING, cast

import pytest
from serial.tools.list_ports_common import ListPortInfo

from msl.equipment import Connection, Equipment, MSLConnectionError, MSLTimeoutError, Serial
from msl.equipment.interfaces.serial import (
    _init_serial,  # pyright: ignore[reportPrivateUsage]
    find_port,
    find_ports,
    parse_serial_address,
)

if TYPE_CHECKING:
    from conftest import PTYServer
    from tests.protocol_mock import SerialServer


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
        "COM?",
        "ASRL?:",
        "?::",
        "ASRL/mock::INSTR",
        "mock://",
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
        ("COM/mock://", "mock://"),
        ("ASRL/mock://", "mock://"),
        ("ASRLCOM/mock://::INSTR", "mock://"),
        ("COM?::VID=1234&PID=4321", "?::VID=1234&PID=4321"),
        ("ASRL?::can be anything\\/:!@#$%^&*()}{,.-=+::INSTR", "?::can be anything\\/:!@#$%^&*()}{,.-=+::INSTR"),
    ],
)
def test_parse_address_valid(address: str, expected: str) -> None:
    parsed = parse_serial_address(address)
    assert parsed is not None
    assert parsed.url == expected


@pytest.mark.skipif(pty is None, reason="pty is not available")
def test_pty_session(pty_server: type[PTYServer]) -> None:
    term = b"\r\n"
    with pty_server(term=term) as server:
        c = Connection(
            f"ASRL{server.name}",
            termination=term,
            timeout=0.2,
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
        with pytest.raises(MSLTimeoutError, match=r"after 0.2 second\(s\)"):
            _ = dev.read(size=n + 1)

        with pytest.raises(MSLConnectionError, match=r"max_read_size is 65536 bytes, requesting 65537 bytes"):
            _ = dev.read(size=dev.max_read_size + 1)  # requesting more bytes than are maximally allowed

        assert dev.read() == "123.456\r\n"  # clear the buffer

        dev.max_read_size = 10
        assert dev.write(b"a" * 999) == 999 + len(term)
        with pytest.raises(MSLConnectionError, match=r"RuntimeError: len\(message\) \[1001\] > max_read_size \[10\]"):
            _ = dev.read()  # requesting more bytes than are maximally allowed

        dev.max_read_size = 1 << 16
        assert dev.read() == ("a" * 999) + term.decode()  # clear the buffer

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
def test_pty_timeout(pty_server: type[PTYServer]) -> None:
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
def test_pty_logging(pty_server: type[PTYServer], caplog: pytest.LogCaptureFixture) -> None:
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
def test_pty_terminator(term: bytes, pty_server: type[PTYServer]) -> None:
    with pty_server(term=term) as server:
        c = Connection(f"ASRL{server.name}", termination=term)
        dev: Serial
        with c.connect() as dev:
            assert dev.read_termination == term
            assert dev.write_termination == term
            assert dev.query("hello", decode=False) == b"hello" + term


def test_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid Serial address 'bad'"):
        _ = Serial(Equipment(connection=Connection("bad")))


@pytest.mark.parametrize("address", ["COM?::VID=1234&PID=4321", "ASRL?::Company Name"])
def test_cannot_find(address: str) -> None:
    with pytest.raises(ValueError, match=r"^Cannot find"):
        _ = Serial(Equipment(connection=Connection(address)))


@pytest.mark.parametrize("address", ["COM?::", "ASRL?::"])
def test_cannot_find_empty_search(address: str) -> None:
    with pytest.raises(ValueError, match=r"Must specify a search pattern for the Serial port"):
        _ = Serial(Equipment(connection=Connection(address)))


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


def test_mock_session() -> None:
    term = b"\r\n"
    c = Connection(
        "ASRL/mock://",
        termination=term,
        timeout=0.02,
        max_read_size=1 << 16,
    )

    dev: Serial = c.connect()
    server = cast("SerialServer", cast("object", dev.serial))

    assert dev.read_termination == term
    assert dev.write_termination == term

    assert dev.query("hello") == "hello\r\n"

    n = dev.write("hello")
    assert dev.read(size=n) == "hello\r\n"

    assert dev.write("x" * 4096) == 4096 + len(term)
    assert dev.read() == "x" * 4096 + term.decode()

    assert dev.write("123.456") == 9
    server.add_response(b"x" * 9)
    with pytest.raises(MSLTimeoutError, match=r"after 0.02 second\(s\)"):
        _ = dev.read(size=10, decode=False)
    assert dev.read(size=9) == "x" * 9  # clear the buffer

    with pytest.raises(MSLConnectionError, match=r"max_read_size is 65536 bytes, requesting 65537 bytes"):
        _ = dev.read(size=dev.max_read_size + 1)  # requesting more bytes than are maximally allowed

    dev.max_read_size = 10
    assert dev.write(b"a" * 999) == 999 + len(term)
    with pytest.raises(MSLConnectionError, match=r"RuntimeError: len\(message\) \[1001\] > max_read_size \[10\]"):
        _ = dev.read()  # requesting more bytes than are maximally allowed
    assert dev.read() == ("a" * 999) + term.decode()  # clear the buffer

    dev.max_read_size = 1000
    assert dev.write(b"021.3" + term + b",054.2") == 15
    assert dev.read() == "021.3\r\n"  # read until first `term`
    assert dev.read() == ",054.2\r\n"  # read until second `term`

    server.add_response(b"1/0")
    with pytest.raises(MSLConnectionError, match=r"ZeroDivisionError"):
        _ = dev.read()

    assert dev.write(b"021.3" + term + b",054.2" + term) == 15
    assert dev.read(size=1) == "0"
    assert dev.read(size=3) == "21."
    assert dev.read(size=2) == "3\r"
    assert dev.read(size=2) == "\n,"
    assert dev.read(size=1) == "0"
    assert dev.read(size=1) == "5"
    assert dev.read(size=1) == "4"
    assert dev.read() == ".2\r\n"

    dev.timeout = None
    assert dev.timeout is None
    assert dev.write("hi") == 4
    assert dev.read() == "hi\r\n"

    dev.disconnect()


def test_find_port_find_ports(caplog: pytest.LogCaptureFixture) -> None:
    a = ListPortInfo("/dev/ttyS1")
    a.hwid = "VID:PID"
    a.description = "Hello"

    b = ListPortInfo("/dev/ttyUSB0")
    b.hwid = "ABC"
    b.manufacturer = "Company"
    b.description = "Ignored"

    c = ListPortInfo("no hwid, so not included")

    d = ListPortInfo("COM5")
    d.hwid = "Windows port"
    d.manufacturer = "Intel"
    d.product = "XY"
    d.description = "Ignored"

    e = ListPortInfo("COM3")
    e.hwid = "Some ID"
    e.manufacturer = "MSL"
    e.product = "N"
    e.serial_number = "Z"
    e.description = "Ignored"

    ports = list(find_ports([a, b, c, d, e]))
    assert len(ports) == 4

    assert ports[0].address == "ASRL/dev/ttyS1"
    assert ports[0].description == "Hello VID:PID"
    assert ports[0].device == "/dev/ttyS1"

    assert ports[1].address == "ASRL/dev/ttyUSB0"
    assert ports[1].description == "Company ABC"
    assert ports[1].device == "/dev/ttyUSB0"

    assert ports[2].address == "COM5"
    assert ports[2].description == "Intel XY Windows port"
    assert ports[2].device == "COM5"

    assert ports[3].address == "COM3"
    assert ports[3].description == "MSL N Z Some ID"
    assert ports[3].device == "COM3"

    with pytest.raises(ValueError, match=r"^Cannot find a Serial port for the address '/dev/ttyS1'$"):
        _ = find_port("ID564", "/dev/ttyS1", [ListPortInfo("hwid is n/a")])

    with pytest.raises(ValueError, match=r"^Cannot find") as exc:
        _ = find_port("ID564", "COM6", [a, b, c, d, e])

    lines = str(exc.value).splitlines()
    assert lines == [
        "Cannot find a Serial port for the address 'COM6', the following descriptions are available",
        "  Hello VID:PID",
        "  Company ABC",
        "  Intel XY Windows port",
        "  MSL N Z Some ID",
    ]

    with caplog.at_level("DEBUG", "msl.equipment"):
        assert find_port("ABC", "Ignored", [a, b, c, d, e]) == "/dev/ttyUSB0"
        assert caplog.messages == ["Searching for Serial ports", "Found matching Serial port '/dev/ttyUSB0'"]
