from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from msl.equipment import FTDI, Connection, Equipment, MSLConnectionError, MSLTimeoutError
from msl.equipment.interfaces.ftdi import (
    FT232A,
    FT2232H,
    ParsedFTDIAddress,
    _ftdi_232am_baud_to_divisor,  # pyright: ignore[reportPrivateUsage]
    _ftdi_232bm_2232h_baud_to_divisor,  # pyright: ignore[reportPrivateUsage]
    _get_ftdi_divisor,  # pyright: ignore[reportPrivateUsage]
    parse_ftdi_address,
)

if TYPE_CHECKING:
    from tests.conftest import USBBackend

FTX = 0x1000


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("", None),
        ("USB::123::456", None),
        ("GPIB::123::456::abc", None),
        ("USB::abc::456::123", None),
        ("FTDI::x::456::abc", None),
        ("FTDI::1::x::abc", None),
        ("FTDI::1::2::index=#", None),
        ("FTDI::123::456::abc", ParsedFTDIAddress(0, 123, 456, "abc", None)),
        ("FTDI::123::456::abc::1", ParsedFTDIAddress(0, 123, 456, "abc", None)),
        ("FTDI2::0x123::0x456::abc", ParsedFTDIAddress(2, 0x123, 0x456, "abc", None)),
        ("FTDI3::1::2::index=8", ParsedFTDIAddress(3, 1, 2, "", 8)),
    ],
)
def test_parse_usb_address(address: str, expected: ParsedFTDIAddress | None) -> None:
    assert parse_ftdi_address(address) == expected


def test_get_ftdi_divisor_sio() -> None:
    assert _get_ftdi_divisor(300, FT232A - 1) == 0
    assert _get_ftdi_divisor(9600, FT232A - 1) == 5


def test_baudrate_out_of_range() -> None:
    with pytest.raises(ValueError, match=r"Invalid baudrate 10, must be one of"):
        _ = _get_ftdi_divisor(10, FT232A - 1)

    with pytest.raises(ValueError, match=r"Invalid baudrate 3100000, must be < 3.0 MBd"):
        _ = _get_ftdi_divisor(3_100_000, FT232A)

    with pytest.raises(ValueError, match=r"Invalid baudrate 10, must be > 183.1 Bd"):
        _ = _get_ftdi_divisor(10, FT232A)

    # since baudrate < 1200, even though we specify a high-speed chip the text
    # "732.4 Bd" (12e6/16384=732.4) is not in the error message
    with pytest.raises(ValueError, match=r"Invalid baudrate 183, must be > 183.1 Bd"):
        _ = _get_ftdi_divisor(183, FT2232H)

    with pytest.raises(ValueError, match=r"Invalid baudrate 13000000, must be < 12.0 MBd"):
        _ = _get_ftdi_divisor(int(13e6), FT2232H)

    with pytest.raises(ValueError, match=r"not within 3\%"):
        _ = _get_ftdi_divisor(2_439_862, FT232A)


# Section 4.2: Aliasing Using the Original Sub-Integer Divisors
# https://www.ftdichip.com/Support/Knowledgebase/index.html?an232b_05calc.htm
@pytest.mark.parametrize(
    ("baudrate", "closest", "n", "sub_divisor"),
    [
        (56_700, 53.0, 53, 0b0000_0000_0000_0000),  # 3e6/56_700 = 52.91005291005291
        (490_000, 6.125, 6, 0b1100_0000_0000_0000),  # 3e6/490_000 = 6.122448979591836
        (60_800, 49.25, 49, 0b1000_0000_0000_0000),  # 3e6/60_800 = 49.3421052631579
        (50_300, 59.5, 59, 0b0100_0000_0000_0000),  # 3e6/50_300 = 59.642147117296226
        (2_100_000, 1.5, 1, 0b0000_0000_0000_0000),  # 2 MBaud is a special case
        (2_900_000, 1.0, 0, 0b0000_0000_0000_0000),  # 3 MBaud is a special case
    ],
)
def test_ftdi_232am_baud_to_divisor(baudrate: int, closest: float, n: int, sub_divisor: int) -> None:
    actual, divisor = _ftdi_232am_baud_to_divisor(baudrate)
    assert actual == round(3e6 / closest)
    expected_divisor = n
    expected_divisor |= sub_divisor
    assert divisor == expected_divisor


@pytest.mark.parametrize(
    ("baudrate", "closest", "n", "sub_divisor"),
    [
        (197_000, 15.25, 15, 0b0_1000_0000_0000_0000),  # 3e6/197_000 = 15.228426395939087
        (18_200, 164.875, 164, 0b1_1100_0000_0000_0000),  # 3e6/18_200 = 164.83516483516485
        (36_100, 83.125, 83, 0b0_1100_0000_0000_0000),  # 3e6/36_100 = 83.10249307479225
    ],
)
def test_ftdi_232bm_2232h_baud_to_divisor(baudrate: int, closest: float, n: int, sub_divisor: int) -> None:
    actual, divisor = _ftdi_232bm_2232h_baud_to_divisor(baudrate, FTX)
    assert actual == round(3e6 / closest)
    expected_divisor = n
    expected_divisor |= sub_divisor
    assert divisor == expected_divisor


@pytest.mark.parametrize(
    ("baudrate", "closest", "n", "sub_divisor"),
    [
        (197_000, 60.875, 60, 0b01_1100_0000_0000_0000),  # 12e6/197_000 = 60.91370558375635
        (114_825, 104.5, 104, 0b00_0100_0000_0000_0000),  # 12e6/114_825 = 104.50685826257349
        (9_549, 1256.625, 1256, 0b01_0100_0000_0000_0000),  # 12e6/9_549 = 1256.6760917373547
    ],
)
def test_ftdi_232bm_2232h_baud_to_divisor_hs(baudrate: int, closest: float, n: int, sub_divisor: int) -> None:
    actual, divisor = _ftdi_232bm_2232h_baud_to_divisor(baudrate, FT2232H)
    assert actual == round(12e6 / closest)
    expected_divisor = n
    expected_divisor |= sub_divisor
    expected_divisor |= 0b10_0000_0000_0000_0000  # MSB set to 1 for high-speed chips
    assert divisor == expected_divisor


# Standard divisors (valid for "original" and "addition" sub-integer divisors)
# Section 4.2: Aliasing Using the Original Sub-Integer Divisors (e.g., FT232A)
# Section 4.3: Aliasing Using the Additional Sub-Integer Divisors (e.g., FTX)
# https://www.ftdichip.com/Documents/AppNotes/AN_120_Aliasing_VCP_Baud_Rates.pdf
@pytest.mark.parametrize("device_version", [FT232A, FTX])
@pytest.mark.parametrize(
    ("baudrate", "divisor"),
    [
        (200, 0x3A98),  # 3e6/200=15000 => hex(15000)=0x3A98
        (300, 0x2710),
        (600, 0x1388),
        (1_200, 0x09C4),
        (2_400, 0x04E2),
        (4_800, 0x0271),
        (9_600, 0x4138),
        (19_200, 0x809C),
        (38_400, 0xC04E),
        (57_600, 0xC034),
        (57_692, 0x0034),
        (115_200, 0x001A),
        (115_384, 0x001A),
        (230_400, 0x000D),
        (230_769, 0x000D),
        (460_800, 0x4006),
        (461_538, 0x4006),
        (921_600, 0x8003),
        (923_076, 0x8003),
        (1_000_000, 0x0003),
        (1_500_000, 0x0002),
        (2_000_000, 0x0001),
        (3_000_000, 0x0000),
        (14_406, 0x80D0),
        (197_000, 0x800F),
    ],
)
def test_standard_divisors(device_version: int, baudrate: int, divisor: int) -> None:
    assert _get_ftdi_divisor(baudrate, device_version) == divisor


# High-speed divisors
# Section 4.4: Aliasing the FT232H, FT2232H and FT4232H for Baud Rates up to 12MBaud
# https://www.ftdichip.com/Documents/AppNotes/AN_120_Aliasing_VCP_Baud_Rates.pdf
@pytest.mark.parametrize(
    ("baudrate", "divisor"),
    [
        (1_200, 0x2710),
        (2_400, 0x1388),
        (4_800, 0x09C4),
        (9_600, 0x04E2),
        (19_200, 0x0271),
        (38_400, 0x4138),
        (76_923, 0x009C),  # typo in FTDI doc?
        (153_846, 0x004E),  # typo in FTDI doc?
        (230_769, 0x0034),
        (461_538, 0x001A),
        (923_077, 0x000D),
        (1_846_153, 0x4006),
        (3_692_308, 0x8003),
        (1_000_000, 0x000C),
        (2_000_000, 0x0006),
        (4_000_000, 0x0003),
        (6_000_000, 0x0002),
        (8_000_000, 0x0001),
        (12_000_000, 0x0000),
        (57_623, 0x80D0),
        (5_500_000, 0xC002),
    ],
)
def test_standard_divisors_high_speed(baudrate: int, divisor: int) -> None:
    assert _get_ftdi_divisor(baudrate, FT2232H) == divisor | 1 << 17  # MSB must be 1 for high-speed chips


def test_invalid_ftdi_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid FTDI address"):
        _ = FTDI(Equipment(connection=Connection("USB::1::2::x")))


def test_invalid_ftdi_driver_number() -> None:
    with pytest.raises(ValueError, match=r"Invalid FTDI driver number 1"):
        _ = FTDI(Equipment(connection=Connection("FTDI1::1::2::x")))


def test_connection_properties(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection(
        "FTDI::1::2::x",
        usb_backend=usb_backend,
        timeout=5.1,
        baudrate=115200,
        dsr_dtr=True,
        stop_bits=2,
        data_bits=7,
        rts_cts=True,
        parity="even",
        xon_xoff=True,
    )

    caplog.set_level("DEBUG", "msl.equipment")
    caplog.clear()

    device: FTDI
    with c.connect() as device:
        assert device.read_termination is None
        assert device.write_termination is None
        assert device.timeout == 5.1

    assert caplog.messages == [
        "Connecting to FTDI<|| at FTDI::1::2::x>",
        "Connecting to USB<|| at FTDI::1::2::x>",
        "FTDI<||>.ctrl_transfer(0x40, 0x03, 0x001A, 0x0001, None, 5100)",  # set baudrate to 115200
        "FTDI<||>.ctrl_transfer(0x40, 0x04, 0x1207, 0x0001, None, 5100)",  # setting parity, data bits, stop bits
        "FTDI<||>.ctrl_transfer(0x40, 0x02, 0x0000, 0x0001, None, 5100)",  # default flow control is None
        "FTDI<||>.ctrl_transfer(0x40, 0x02, 0x1311, 0x0401, None, 5100)",  # enable xon_xoff with xon=17, xoff=19
        "FTDI<||>.ctrl_transfer(0x40, 0x02, 0x0000, 0x0201, None, 5100)",  # enable dsr_dtr
        "FTDI<||>.ctrl_transfer(0x40, 0x02, 0x0000, 0x0101, None, 5100)",  # enable rts_cts
        "Disconnected from USB<|| at FTDI::1::2::x>",
        "Disconnected from FTDI<|| at FTDI::1::2::x>",
    ]


def test_connection_without_properties(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    caplog.set_level("DEBUG", "msl.equipment")
    caplog.clear()

    device: FTDI
    with c.connect() as device:
        assert device.read_termination is None
        assert device.write_termination is None
        assert device.timeout is None

    assert caplog.messages == [
        "Connecting to FTDI<|| at FTDI::1::2::x>",
        "Connecting to USB<|| at FTDI::1::2::x>",
        "FTDI<||>.ctrl_transfer(0x40, 0x03, 0x4138, 0x0001, None, 0)",  # set baudrate to 9600
        "FTDI<||>.ctrl_transfer(0x40, 0x04, 0x0008, 0x0001, None, 0)",  # setting parity, data bits, stop bits
        "FTDI<||>.ctrl_transfer(0x40, 0x02, 0x0000, 0x0001, None, 0)",  # default flow control
        "Disconnected from USB<|| at FTDI::1::2::x>",
        "Disconnected from FTDI<|| at FTDI::1::2::x>",
    ]


def test_invalid_data_bits(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend, data_bits=6)
    with pytest.raises(ValueError, match=r"either 7 or 8"), c.connect():
        pass


def test_invalid_latency_timer(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device:
        device.set_latency_timer(100)

        with pytest.raises(ValueError, match=r"Invalid latency timer"):
            device.set_latency_timer(256)


def test_ctrl_transfer_in(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device:
        usb_backend.add_ctrl_response(b"\x10")
        assert device.get_latency_timer() == 16

        usb_backend.add_ctrl_response(b"\x11\x60")
        assert device.poll_status() == (17, 96)


def test_ctrl_transfer_in_sio_chip(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", device_version=FT232A - 1)
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device:
        usb_backend.clear_ctrl_response_queue()  # ctrl_transfer is not actually sent to device
        assert device.get_latency_timer() == 16

        usb_backend.add_ctrl_response(b"\x11")
        assert device.poll_status() == (17, 0)


def test_ctrl_transfer_out(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x", device_version=FT232A)
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device, caplog.at_level("DEBUG", "msl.equipment"):
        device.set_dtr(active=True)
        device.set_dtr(active=False)
        device.set_rts(active=True)
        device.set_rts(active=False)
        device.set_baud_rate(9600)
        device.purge_buffers()
        device.reset_device()

        assert caplog.messages == [
            "FTDI<||>.ctrl_transfer(0x40, 0x01, 0x0101, 0x0001, None, 0)",  # activate DTR
            "FTDI<||>.ctrl_transfer(0x40, 0x01, 0x0100, 0x0001, None, 0)",  # deactivate DTR
            "FTDI<||>.ctrl_transfer(0x40, 0x01, 0x0202, 0x0001, None, 0)",  # activate RTS
            "FTDI<||>.ctrl_transfer(0x40, 0x01, 0x0200, 0x0001, None, 0)",  # deactivate RTS
            "FTDI<||>.ctrl_transfer(0x40, 0x03, 0x4138, 0x0000, None, 0)",  # set baud rate to 9600
            "FTDI<||>.ctrl_transfer(0x40, 0x00, 0x0001, 0x0001, None, 0)",  # purge host-to-ftdi buffer
            "FTDI<||>.ctrl_transfer(0x40, 0x00, 0x0002, 0x0001, None, 0)",  # purge ftdi-to-host buffer
            "FTDI<||>.ctrl_transfer(0x40, 0x00, 0x0000, 0x0001, None, 0)",  # reset
        ]


def test_set_latency_timer_sio(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", device_version=FT232A - 1)
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device:
        # setting to 16 is okay
        device.set_latency_timer(16)

        # anything else is an error
        with pytest.raises(MSLConnectionError, match=r"fixed at 16 ms"):
            device.set_latency_timer(165)


def test_read_write(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device:
        assert device.timeout is None

        # writing b"hello" sets the line status (second byte) to have a bit mask that enables some of the error bits
        assert ord("e") & 0x8E
        assert device.write(b"hello") == 5
        with pytest.raises(MSLConnectionError, match=r"bit mask of the line-status byte is 0b01100101"):
            _ = device.read(size=5)

        status_bytes = bytes([17, 96])  # modem=17, line=96

        usb_backend.add_bulk_response(status_bytes + b"x")
        assert device.read(size=1, decode=False) == b"x"

        response = (
            b"\x06\x00T\x00\x81\x01\xcc\xba0\x02SCC201\x00\x00\x10\x00\x05\x01\x03\x00APT Stepper Controller"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00APT Stepper \x03\x00\x01\x00\x01\x00"
        )

        usb_backend.add_bulk_response(status_bytes)
        usb_backend.add_bulk_response(status_bytes)
        usb_backend.add_bulk_response(status_bytes + response[:1])
        usb_backend.add_bulk_response(status_bytes + response[1:10])
        usb_backend.add_bulk_response(status_bytes + response[10:20])
        usb_backend.add_bulk_response(status_bytes + response[20:53])
        usb_backend.add_bulk_response(status_bytes + response[53:60])
        usb_backend.add_bulk_response(status_bytes + response[60:])
        usb_backend.add_bulk_response(status_bytes)
        usb_backend.add_bulk_response(status_bytes)
        assert device.read(size=90, decode=False) == response

        usb_backend.clear_bulk_response_queue()

        usb_backend.add_bulk_response(status_bytes)
        usb_backend.add_bulk_response(status_bytes + response[:1])
        usb_backend.add_bulk_response(status_bytes + response[1:10])
        usb_backend.add_bulk_response(status_bytes)  # stops reading here since size=None
        usb_backend.add_bulk_response(status_bytes + response[10:])
        assert device.read(size=None, decode=False) == response[:10]

        usb_backend.clear_bulk_response_queue()

        device.max_read_size = 32
        usb_backend.add_bulk_response(status_bytes + response[:40])
        with pytest.raises(MSLConnectionError, match=r"len\(message\) \[40\] > max_read_size \[32\]"):
            _ = device.read(size=32)

        usb_backend.clear_bulk_response_queue()

        device.max_read_size = 1024
        device.timeout = 0.06  # usb_backend.bulk_read() sleeps for 0.05 seconds per read
        usb_backend.add_bulk_response(status_bytes + b"sleep")
        usb_backend.add_bulk_response(status_bytes + b"sleep")
        with pytest.raises(MSLTimeoutError):
            _ = device.read(size=90)


def test_write_sio(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", device_version=FT232A - 1)
    c = Connection("FTDI::1::2::x", usb_backend=usb_backend)

    device: FTDI
    with c.connect() as device, pytest.raises(MSLConnectionError, match=r"FTDI chip requires a header byte"):
        _ = device.write(b"hi")
