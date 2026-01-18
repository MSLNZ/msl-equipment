from __future__ import annotations

import sys
from array import array
from typing import TYPE_CHECKING

import pytest
import usb.util  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]

from msl.equipment import USB, Connection, Equipment, MSLConnectionError, MSLTimeoutError
from msl.equipment.interfaces.usb import (
    REGEX,
    ParsedUSBAddress,
    _endpoint,  # pyright: ignore[reportPrivateUsage]
    _find_device,  # pyright: ignore[reportPrivateUsage]
    _is_linux_and_not_sudo,  # pyright: ignore[reportPrivateUsage]
    _usb_backend,  # pyright: ignore[reportPrivateUsage]
    find_usb,
    parse_usb_address,
)

if TYPE_CHECKING:
    from tests.conftest import USBBackend

IS_WINDOWS = sys.platform == "win32"

ENDPOINT_IN = int(usb.util.ENDPOINT_IN)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
ENDPOINT_OUT = int(usb.util.ENDPOINT_OUT)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
ENDPOINT_TYPE_BULK = int(usb.util.ENDPOINT_TYPE_BULK)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
ENDPOINT_TYPE_INTR = int(usb.util.ENDPOINT_TYPE_INTR)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


def test_get_usb_backend_invalid() -> None:
    with pytest.raises(ValueError, match=r"The requested 'abc' PyUSB backend is invalid"):
        _ = _usb_backend("abc")


def test_get_usb_backend_cannot_load() -> None:
    with pytest.raises(ValueError, match=r"Cannot load the requested 'openusb' PyUSB backend"):
        _ = _usb_backend("openusb")


@pytest.mark.skipif(sys.platform == "darwin" and sys.version_info[:2] == (3, 8), reason="libusb1 not available in CI")
def test_get_usb_backend_success() -> None:
    assert _usb_backend("libusb1") is not None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("", None),
        ("USB::123::456", None),
        ("GPIB::123::456::abc", None),
        ("USB::abc::456::123", None),
        ("USB::123::abc::456", None),
        ("USB::123::456::abc", ParsedUSBAddress(123, 456, "abc", 0)),
        ("USB::123::456::abc::INSTR", ParsedUSBAddress(123, 456, "abc", 0)),
        ("USB::123::456::abc::0::INSTR", ParsedUSBAddress(123, 456, "abc", 0)),
        ("USB::123::456::abc::", ParsedUSBAddress(123, 456, "abc", 0)),
        ("USB::123::456::abc::RAW", ParsedUSBAddress(123, 456, "abc", 0)),
        ("usb0::123::456::ABC::raw", ParsedUSBAddress(123, 456, "ABC", 0)),
        ("USB3::0x012f::0x04a6::index2::11::RAW", ParsedUSBAddress(0x012F, 0x04A6, "index2", 11)),
        ("USB10::0X1::0X2::3:4::5::Whatever", ParsedUSBAddress(1, 2, "3:4", 5)),
        ("FTDI::123::456::abc", ParsedUSBAddress(123, 456, "abc", 0)),
        ("fTdi0::123::456::abc", ParsedUSBAddress(123, 456, "abc", 0)),
    ],
)
def test_parse_usb_address(address: str, expected: ParsedUSBAddress | None) -> None:
    assert parse_usb_address(address) == expected


@pytest.mark.parametrize(
    ("address", "matches"),
    [
        # The USB class should not be used for a USB-TMC address
        ("USB::123::456::abc", False),
        ("USB::123::456::abc::INSTR", False),
        ("USB::123::456::abc::0::INSTR", False),
        ("usb0::0x0123::0x0456::abc::0::instr", False),
        # Not a valid USB address
        ("USB::123::456", False),
        ("USBx::123::456::abc::RAW", False),
        ("xxx::123::456::abc", False),
        ("COM3", False),
        # Valid
        ("USB::123::456::abc::", True),
        ("USB::123::456::abc::RAW", True),
        ("usb0::123::456::ABC::raw", True),
        ("USB3::0x012f::0x04a6::2::11::RAW", True),
        ("USB1::1::0x2::3:4::RAW", True),  # serial contains a colon
        ("USB10::1::0x2::3:4::5::RAW", True),  # serial contains a colon, include interface number
    ],
)
def test_regex(address: str, *, matches: bool) -> None:
    if matches:
        assert REGEX.match(address) is not None
    else:
        assert REGEX.match(address) is None


def test_find_device_ignore_serial(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "whatever")
    parsed = ParsedUSBAddress(1, 2, "IGNORE", 0)
    assert _find_device(parsed, backend=usb_backend) is not None


def test_find_device_bus_address(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "whatever")

    parsed = ParsedUSBAddress(1, 2, "bus=1,address=1", 0)
    assert _find_device(parsed, backend=usb_backend) is not None

    parsed = ParsedUSBAddress(1, 2, "bus=1,address=2", 0)
    assert _find_device(parsed, backend=usb_backend) is None


def test_invalid_usb_address() -> None:
    with pytest.raises(ValueError, match=r"GPIB::5"):
        _ = USB(Equipment(connection=Connection("GPIB::5")))


def test_invalid_backend_string() -> None:
    with pytest.raises(ValueError, match=r"'xxx' PyUSB backend is invalid"):
        _ = Connection("USB::1::2::serial::RAW", usb_backend="xxx").connect()


def test_no_backend_available(usb_backend: USBBackend) -> None:
    # By not calling usb_backend.add_device() the mocked USB backend simulates no backend library
    with pytest.raises(MSLConnectionError, match=r"A PyUSB backend is not available"):
        _ = Connection("USB::1::2::serial::RAW", usb_backend=usb_backend).connect()


def test_device_not_found(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    with pytest.raises(MSLConnectionError, match=r"The USB device was not found"):
        _ = Connection("USB::1::2::serial::RAW", usb_backend=usb_backend).connect()


def test_device_found(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    address = "USB::1::2::x::RAW"
    c = Connection(address, usb_backend=usb_backend)

    caplog.set_level("DEBUG", "msl.equipment")
    caplog.clear()

    device = c.connect()
    device.disconnect()
    device.disconnect()  # multiple times is okay, logs Disconnected once
    device.disconnect()

    assert caplog.messages == [
        f"Connecting to USB<|| at {address}>",
        f"Disconnected from USB<|| at {address}>",
    ]


def test_configuration_value_properties_invalid(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    with pytest.raises(MSLConnectionError, match=r"Invalid configuration value 4"):
        _ = Connection("USB::1::2::x::RAW", usb_backend=usb_backend, bConfigurationValue=4).connect()


def test_set_configuration_raises(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "config-not-set")
    # The match value is defined in USBBackend.get_configuration_descriptor()
    with pytest.raises(MSLConnectionError, match=r"Mocked message from pyUSB"):
        _ = Connection("USB::1::2::config-not-set::RAW", usb_backend=usb_backend).connect()


def test_connection_properties(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend, timeout=5.1)

    device: USB
    with c.connect() as device:
        assert device.bulk_in_endpoint.address == 0x81
        assert device.bulk_in_endpoint.max_packet_size == 0x0040
        assert device.bulk_in_endpoint.interface_number == 0

        assert device.bulk_out_endpoint.address == 0x02
        assert device.bulk_out_endpoint.max_packet_size == 0x0040
        assert device.bulk_out_endpoint.interface_number == 0

        assert device.intr_in_endpoint is None
        assert device.intr_out_endpoint is None

        assert device.timeout == 5.1
        assert device._timeout_ms == 5100  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        device.timeout = None
        assert device._timeout_ms == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001


@pytest.mark.parametrize(("direction", "name"), [(ENDPOINT_IN, "IN"), (ENDPOINT_OUT, "OUT")])
def test_get_endpoint_info_bulk_missing(usb_backend: USBBackend, direction: int, name: str) -> None:
    usb_backend.add_device(1, 2, "x")
    cls = USB(Equipment(connection=Connection("USB::1::2::x::RAW", usb_backend=usb_backend)))
    with pytest.raises(MSLConnectionError, match=rf"Cannot find a bulk-{name} endpoint"):
        _ = _endpoint(cls, [], direction, ENDPOINT_TYPE_BULK)


@pytest.mark.parametrize("direction", [ENDPOINT_IN, ENDPOINT_OUT])
def test_get_endpoint_info_interrupt_missing(usb_backend: USBBackend, direction: int) -> None:
    usb_backend.add_device(1, 2, "x")
    cls = USB(Equipment(connection=Connection("USB::1::2::x::RAW", usb_backend=usb_backend)))
    assert _endpoint(cls, [], direction, ENDPOINT_TYPE_INTR) is None


def test_write_read_query(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend)
    with USB(Equipment(connection=c)) as device:
        assert device.write_termination == b"\r\n"
        assert device.write("measurement\r\n") == 13
        assert device.read(size=7) == "measure"
        assert device.read(size=6) == "ment\r\n"  # cSpell: ignore ment

        assert device.write("x" * 254) == 256

        assert device.query("echo", decode=False) == b"echo\r\n"

        # writes in `max_packet_size` so the first x's are not included in the return value
        msg = (b"x" * device.bulk_out_endpoint.max_packet_size) + b"yyy\r\n"
        assert device.write(msg) == device.bulk_out_endpoint.max_packet_size + 5
        assert device.read(decode=False) == b"yyy\r\n"

        device.max_read_size = 4
        with pytest.raises(MSLConnectionError, match=r"max_read_size"):
            _ = device.query("more than 4 characters")

        device.max_read_size = 1000
        assert device.read(decode=False) == b"more than 4 characters\r\n"

        device.timeout = 0.06  # usb_backend.bulk_read() sleeps for 0.05 seconds per read
        device.read_termination = None
        usb_backend.add_bulk_response(b"sleep")
        usb_backend.add_bulk_response(b"sleep")
        with pytest.raises(MSLTimeoutError):
            _ = device.read(size=10)

        device.write_termination = None
        assert device.write(b"") == 0


def test_ctrl_transfer(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend)
    with USB(Equipment(connection=c)) as device:
        assert device.ctrl_transfer(USB.CtrlDirection.OUT, 0x06) == 4
        assert device.ctrl_transfer(USB.CtrlDirection.IN, 0, data_or_length=1) == array("B", [0])


def test_ctrl_transfer_timeout(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend)
    with USB(Equipment(connection=c)) as device, pytest.raises(MSLTimeoutError):
        _ = device.ctrl_transfer(9999, 6, 0, 0, "test")


def test_ctrl_transfer_usb_error(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend)
    with USB(Equipment(connection=c)) as device, pytest.raises(MSLConnectionError, match=r"Transfer error"):
        _ = device.ctrl_transfer(1234, 6, 0, 0, "test")


def test_build_request_type() -> None:
    assert USB.build_request_type(USB.CtrlDirection.IN, USB.CtrlType.VENDOR, USB.CtrlRecipient.ENDPOINT) == 194


def test_clear_halt_reset_device_version(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x::RAW", usb_backend=usb_backend)
    with USB(Equipment(connection=c)) as device:
        assert device.device_version == 0x1001

        with caplog.at_level("DEBUG", "msl.equipment"):
            device.clear_halt(device.bulk_in_endpoint)
            device.reset_device()
            assert caplog.messages == [
                "USB<||>.clear_halt(0x81)",
                "USB<||>.reset_device()",
            ]


def test_find_usb_invalid_backend(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG", "msl.equipment")
    caplog.clear()

    assert len(find_usb(usb_backend="pie")) == 0

    assert caplog.messages == [
        "Searching for USB devices (backend='pie')",
        "ValueError: The requested 'pie' PyUSB backend is invalid, must be one of: libusb0, libusb1, openusb",
    ]


def test_find_usb(usb_backend: USBBackend) -> None:
    usb_backend.add_device(0x0403, 1, "a")
    usb_backend.add_device(1, 2, "b")
    usb_backend.add_device(3, 4, "c", is_usb_tmc=True)
    usb_backend.add_device(5, 6, "d", is_not_raw=True)
    usb_backend.add_device(7, 8, "bus=1,address=1")
    usb_backend.add_device(9, 10, "e", alternate_setting=3)
    usb_backend.add_device(11, 12, "f")
    usb_backend.add_device(11, 12, "f")
    usb_backend.add_device(11, 12, "f", bus=None, address=None)
    usb_backend.add_device(11, 12, "")
    usb_backend.add_device(13, 14, "g", num_configurations=2)
    usb_backend.add_device(0x0403, 2, "")

    sudo_tip = ", try running as sudo or create a udev rule" if _is_linux_and_not_sudo() else ""
    d2xx_tip = ", use FTDI2 address (if available) or use Zadig to replace driver" if IS_WINDOWS else ""

    devices = find_usb(usb_backend=usb_backend)
    assert len(devices) == 12
    assert devices[0].visa_address == "FTDI::0x0403::0x0001::a"
    assert devices[0].description == "a, a"
    assert devices[1].visa_address == "USB::0x0001::0x0002::b::RAW"
    assert devices[1].description == "b, b"
    assert devices[2].visa_address == "USB::0x0003::0x0004::c::INSTR"
    assert devices[2].description == "c, c"
    assert devices[3].visa_address == "USB::0x0007::0x0008::bus=1,address=1::RAW"
    assert devices[3].description == "bus=1,address=1, bus=1,address=1"
    assert devices[4].visa_address == "USB::0x0009::0x000a::e::RAW"
    assert devices[4].description == "e, e, define bAlternateSetting=3"
    assert devices[5].visa_address == "USB::0x000b::0x000c::bus=1,address=1::RAW"
    assert devices[5].description == "f, f, serial number is 'f' but it is not unique"
    assert devices[6].visa_address == "USB::0x000b::0x000c::bus=1,address=1::RAW"
    assert devices[6].description == "f, f, serial number is 'f' but it is not unique"
    assert devices[7].visa_address == "USB::0x000b::0x000c::IGNORE::RAW"
    assert devices[7].description == "f, f"
    assert devices[8].visa_address == "USB::0x000b::0x000c::bus=1,address=1::RAW"
    assert devices[8].description == "Unknown USB Device" + sudo_tip
    assert devices[9].visa_address == "USB::0x000d::0x000e::bus=1,address=1::RAW"
    assert devices[9].description == "g, g, serial number is 'g' but it is not unique"
    assert devices[10].visa_address == "USB::0x000d::0x000e::bus=1,address=1::RAW"
    assert devices[10].description == "g, g, define bConfigurationValue=1, serial number is 'g' but it is not unique"
    assert devices[11].visa_address == "FTDI::0x0403::0x0002::bus=1,address=1"
    if _is_linux_and_not_sudo():
        assert devices[11].description == "Unknown USB Device" + sudo_tip
    else:
        assert devices[11].description == "Unknown USB Device" + d2xx_tip
