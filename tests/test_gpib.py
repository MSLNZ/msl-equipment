from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from msl.equipment import GPIB, Connection, Equipment, MSLConnectionError
from msl.equipment.interfaces.gpib import (
    ParsedGPIBAddress,
    _convert_timeout,  # pyright: ignore[reportPrivateUsage]
    find_listeners,
    parse_gpib_address,
)
from msl.equipment.interfaces.message_based import MSLTimeoutError

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def mock_gpib() -> Iterator[None]:
    GPIB.gpib_library = None
    os.environ["GPIB_LIBRARY"] = "tests/resources/gpib"
    yield
    GPIB.gpib_library = None
    _ = os.environ.pop("GPIB_LIBRARY")


@pytest.mark.parametrize(
    "address",
    ["", "gpi", "COM2", "ASRL/dev/ttyUSB1", "SDK::filename.so", "SOCKET::192.168.1.100::5000", "Prologix::COM6"],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_gpib_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("GPIB", ParsedGPIBAddress(board=0, name=None, pad=None, sad=None)),
        ("GPIB::", ParsedGPIBAddress(board=0, name=None, pad=None, sad=None)),
        ("GPIB0", ParsedGPIBAddress(board=0, name=None, pad=None, sad=None)),
        ("GPIB3", ParsedGPIBAddress(board=3, name=None, pad=None, sad=None)),
        ("GPIB::voltmeter", ParsedGPIBAddress(board=0, name="voltmeter", pad=None, sad=None)),
        ("GPIB0::voltmeter", ParsedGPIBAddress(board=0, name="voltmeter", pad=None, sad=None)),
        ("GPIB16::dmm34401", ParsedGPIBAddress(board=16, name="dmm34401", pad=None, sad=None)),
        ("GPIB::1", ParsedGPIBAddress(board=0, name=None, pad=1, sad=None)),
        ("GPIB1::1", ParsedGPIBAddress(board=1, name=None, pad=1, sad=None)),
        ("GPIB1::11::111", ParsedGPIBAddress(board=1, name=None, pad=11, sad=111)),
        ("GPIB10::2::96", ParsedGPIBAddress(board=10, name=None, pad=2, sad=96)),
        ("GPIB::1::0::INSTR", ParsedGPIBAddress(board=0, name=None, pad=1, sad=0)),
        ("GPIB2::INTFC", ParsedGPIBAddress(board=2, name=None, pad=None, sad=None)),
        ("gpib1::intfc", ParsedGPIBAddress(board=1, name=None, pad=None, sad=None)),
    ],
)
def test_parse_address_valid(address: str, expected: ParsedGPIBAddress) -> None:
    assert parse_gpib_address(address) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, 0),
        (-1, 0),
        (0, 0),
        (4.1e-6, 1),
        (10e-6, 1),
        (10.1e-6, 2),
        (29.9e-6, 2),
        (30e-6, 2),
        (50e-6, 3),
        (100e-6, 3),
        (123e-6, 4),
        (300e-6, 4),
        (0.0009, 5),
        (0.001, 5),
        (0.002, 6),
        (3e-3, 6),
        (0.005, 7),
        (10e-3, 7),
        (0.025, 8),
        (0.03, 8),
        (0.05, 9),
        (100e-3, 9),
        (0.25, 10),
        (300e-3, 10),
        (0.5, 11),
        (1, 11),
        (1.2, 12),
        (3, 12),
        (5, 13),
        (10.0, 13),
        (25, 14),
        (30, 14),
        (30.001, 15),
        (1e2, 15),
        (299.999, 16),
        (300, 16),
        (301, 17),
        (1.0e3, 17),
        (1001, 17),
        (3600.0, 17),
        (1e9, 17),
    ],
)
def test_convert_timeout(value: float, expected: int) -> None:
    assert _convert_timeout(value) == expected


def test_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid GPIB address"):
        _ = GPIB(Equipment(connection=Connection("TCP::192.168.1.100::5555")))


def test_find_listeners() -> None:
    assert "GPIB_LIBRARY" not in os.environ
    assert GPIB.gpib_library is None
    listeners = find_listeners()
    assert isinstance(listeners, list)
    for listener in listeners:
        assert listener.startswith("GPIB")


def test_mock_find_listeners(mock_gpib: None) -> None:
    assert mock_gpib is None
    assert find_listeners(include_sad=True) == ["GPIB0::5::INSTR", "GPIB15::11::INSTR", "GPIB15::11::123::INSTR"]


def test_mock_read_write(mock_gpib: None) -> None:
    assert mock_gpib is None

    dev: GPIB = Connection("GPIB::5", timeout=1.2).connect()
    assert dev.read_termination is None  # is None unless read_termination is specified as a Connection.properties
    assert dev.write_termination == b"\r\n"
    dev.read_termination = "\0"
    assert dev.read_termination == b"\0"
    dev.read_termination = b"\r"
    assert dev.read_termination == b"\r"
    dev.read_termination = None
    assert dev.read_termination is None

    assert dev.handle == 3
    assert dev.version() == "" if sys.platform == "win32" else "1.2"
    assert dev.timeout == 1.0  # 1.2 becomes 1.0
    assert dev.write("whatever") == 10  # always 10 bytes
    assert dev.read() == "A" * 10
    assert dev.query("10 A's", decode=False) == b"A" * 10
    assert dev.read(size=5) == "A" * 5

    dev.max_read_size = 9
    with pytest.raises(MSLConnectionError, match=r"Maximum read size exceeded"):
        _ = dev.read()

    assert dev.gpib_library is not None
    assert Path(dev.gpib_library.path).name.startswith("gpib")


def test_mock_bad_device_name(mock_gpib: None) -> None:
    assert mock_gpib is None
    with pytest.raises(MSLConnectionError, match=r"name 'bad'"):
        _ = Connection("GPIB::bad").connect()


def test_mock_good_device_name(mock_gpib: None) -> None:
    assert mock_gpib is None
    dev = Connection("GPIB::good").connect()
    assert dev.handle == 2


def test_mock_interface_board(mock_gpib: None) -> None:
    assert mock_gpib is None
    dev = Connection("GPIB6::INTFC").connect()
    assert dev.handle == 6


def test_mock_cannot_get_handle(mock_gpib: None) -> None:
    assert mock_gpib is None
    with pytest.raises(MSLConnectionError, match=r"Cannot acquire a handle"):
        _ = Connection("GPIB3::1").connect()  # raises because board=3


def test_mock_timeout(mock_gpib: None) -> None:
    assert mock_gpib is None
    dev: GPIB = Connection("GPIB::5", timeout=1.2).connect()
    with pytest.raises(MSLTimeoutError, match=r"Timeout occurred after 1.0 second\(s\). If you are confident"):
        _ = dev.clear()


def test_mock_error(mock_gpib: None) -> None:
    assert mock_gpib is None
    dev: GPIB = Connection("GPIB::5").connect()
    match = r"One or more arguments to the function call were invalid \[ibcmd, ibsta:0x8000, iberr:0x4\]"
    with pytest.raises(MSLConnectionError, match=match):
        _ = dev.command(b"foo")


def test_mock_logging(mock_gpib: None, caplog: pytest.LogCaptureFixture) -> None:  # noqa: PLR0915
    assert mock_gpib is None
    with caplog.at_level("DEBUG"):
        dev = GPIB(Equipment(connection=Connection("GPIB::5")))
        assert dev.ask(0) == 0
        # skip clear() and command() since they raise exceptions (tested above)
        assert dev.config(0, 0) == 22
        assert dev.control_atn(0) == 1
        assert dev.control_atn(1) == 10
        assert dev.control_atn(2) == 2
        assert dev.control_atn(3) == 11
        assert dev.control_ren(0) == 22
        assert dev.control_ren(1) == 22
        assert dev.control_ren(5) == 0  # doesn't create a log entry
        assert dev.count() == 10  # doesn't create a log entry
        assert dev.interface_clear() == 29
        assert dev.lines() == 24
        assert dev.listener(5, 0, handle=0) is True
        assert dev.local() == 25
        assert dev.online(state=True) == 26
        assert dev.pass_control() == dev.handle
        assert dev.remote_enable(state=False) == 22
        assert dev.serial_poll() == ord("p")
        assert dev.spoll_bytes() == 30
        assert dev.status() == 0  # doesn't create a log entry
        assert dev.trigger() == 31
        # version() tested above
        assert dev.wait(0) == 32
        assert dev.wait_for_srq() == 32
        assert dev.write_async(b"foo") == 34
        dev.disconnect()
        dev.disconnect()  # multiple times is ok and only logs "Disconnected from ..." once
        dev.disconnect()
        assert dev.gpib_library is not None
        assert len(caplog.messages) == 29
        assert caplog.messages[0] == "Connecting to GPIB<|| at GPIB::5>"
        assert caplog.messages[1] == f"Loaded {dev.gpib_library.path}"
        assert caplog.messages[2] == "gpib.ibdev(0, 5, 0, 0, 1, 0) -> 3"
        assert caplog.messages[3].startswith("gpib.ibask(3, 10,")
        assert caplog.messages[4] == "gpib.ibconfig(3, 3, 0) -> 0x16"
        assert caplog.messages[5].startswith("gpib.ibask(3, 3,")
        assert caplog.messages[6].startswith("gpib.ibask(3, 0,")
        assert caplog.messages[7] == "gpib.ibconfig(3, 0, 0) -> 0x16"
        assert caplog.messages[8] == "gpib.ibgts(3, 0) -> 0x1"
        assert caplog.messages[9] == "gpib.ibcac(3, 0) -> 0xa"
        assert caplog.messages[10] == "gpib.ibgts(3, 1) -> 0x2"
        assert caplog.messages[11] == "gpib.ibcac(3, 1) -> 0xb"
        assert caplog.messages[12] == "gpib.ibconfig(3, 11, 0) -> 0x16"
        assert caplog.messages[13] == "gpib.ibconfig(3, 11, 1) -> 0x16"
        assert caplog.messages[14] == "gpib.ibsic(3,) -> 0x1d"
        assert caplog.messages[15].startswith("gpib.iblines(3, <cpa")
        assert caplog.messages[16].startswith("gpib.ibln(0, 5, 0, <cpa")
        assert caplog.messages[17] == "gpib.ibloc(3,) -> 0x19"
        assert caplog.messages[18] == "gpib.ibonl(3, 1) -> 0x1a"
        assert caplog.messages[19] == "gpib.ibpct(3,) -> 0x1b"
        assert caplog.messages[20] == "gpib.ibconfig(3, 11, 0) -> 0x16"
        assert caplog.messages[21].startswith("gpib.ibrsp(3, <ctypes.c_char_Array_1")
        assert caplog.messages[22].startswith("gpib.ibspb(3, <cpa")
        assert caplog.messages[23] == "gpib.ibtrg(3,) -> 0x1f"
        assert caplog.messages[24] == "gpib.ibwait(3, 0) -> 0x20"
        assert caplog.messages[25] == "gpib.ibwait(3, 4096) -> 0x20"
        assert caplog.messages[26] == "gpib.ibwrta(3, b'foo', 3) -> 0x22"
        assert caplog.messages[27] == "gpib.ibonl(3, 0) -> 0x1a"
        assert caplog.messages[28] == "Disconnected from GPIB<|| at GPIB::5>"
