from __future__ import annotations

import sys
from array import array
from typing import TYPE_CHECKING

import pytest

from msl.equipment import USB, USBTMC, Connection, MSLConnectionError, MSLTimeoutError, RENMode
from msl.equipment.interfaces.usbtmc import Capabilities, _Message  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    from tests.conftest import USBBackend


@pytest.mark.parametrize(
    "address",
    [
        "USB::0x2a2b::0x1122::ABC123",
        "USB6::0x2a2b::0x1122::ABC123",
        "USB::10795::4386::ABC123",
        "USB::0x2a2b::0x1122::ABC123::1",
        "USB::0x2a2b::0x1122::ABC123::INSTR",
        "USB::0x2a2b::0x1122::ABC123::2::INSTR",
    ],
)
def test_usbtmc_address(address: str, usb_backend: USBBackend) -> None:
    usb_backend.add_device(0x2A2B, 0x1122, "ABC123")
    c = Connection(address, usb_backend=usb_backend)
    with c.connect() as device:
        assert isinstance(device, USBTMC)
        assert isinstance(device, USB)  # inheritance


def test_usbtmc_address_raw(usb_backend: USBBackend) -> None:
    usb_backend.add_device(0x2A2B, 0x1122, "ABC123")
    c = Connection("USB::0x2a2b::0x1122::ABC123::RAW", usb_backend=usb_backend)
    with c.connect() as device:
        assert not isinstance(device, USBTMC)
        assert isinstance(device, USB)


@pytest.mark.skipif(sys.platform == "darwin" and sys.version_info[:2] == (3, 8), reason="libusb1 not available in CI")
def test_usbtmc_not_found() -> None:
    c = Connection("USB::0x2a2b::0x1122::ABC123")
    with pytest.raises(MSLConnectionError, match=r"The USB device was not found"):
        _ = c.connect()


def test_capabilities() -> None:  # noqa: PLR0915
    response = array("B", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert not c.accepts_remote_local
    assert not c.accepts_service_request
    assert not c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_488_interface
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_488_interface
    assert c.is_listen_only
    assert c.is_talk_only

    response[0] = 0  # simulate an unsuccessful response
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert not c.accepts_remote_local
    assert not c.accepts_service_request
    assert not c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_488_interface
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 6, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert not c.accepts_term_char
    assert c.accepts_trigger  # is_dt_capable=True OR accepts_interface_trigger=False  => True
    assert c.is_488_interface
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 7, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_488_interface
    assert not c.is_listen_only
    assert not c.is_talk_only

    # enable: indicator pulse, listen only, term char, REN_CONTROL, SR1
    data = [1, 0, 0, 0, 0b00000101, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0b00000010, 0b00000100, 0, 0, 0, 0, 0, 0, 0, 0]
    response = array("B", data)
    c = Capabilities(response)
    assert c.accepts_indicator_pulse
    assert c.accepts_remote_local  # because of REN_CONTROL
    assert c.accepts_service_request  # because SR1
    assert c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_488_interface
    assert c.is_listen_only
    assert not c.is_talk_only

    assert str(c) == (
        "Capabilities(\n"
        "  data=array('B', [1, 0, 0, 0, 5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 4, 0, 0, 0, 0, 0, 0, 0, 0]),\n"
        "  accepts_indicator_pulse=True,\n"
        "  accepts_remote_local=True,\n"
        "  accepts_service_request=True,\n"
        "  accepts_term_char=True,\n"
        "  accepts_trigger=False,\n"
        "  is_488_interface=False,\n"
        "  is_listen_only=True,\n"
        "  is_talk_only=False\n"
        ")"
    )


def test_indicator_pulse(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.accepts_indicator_pulse
        usb_backend.add_ctrl_response(b"\x01")  # STATUS_SUCCESS
        device.indicator_pulse()

        usb_backend.add_ctrl_response(b"\x80")  # STATUS_FAILED
        with pytest.raises(MSLConnectionError, match=r"The request was not successful \[status_code=0x80\]"):
            device.indicator_pulse()

        device.capabilities.accepts_indicator_pulse = False
        with pytest.raises(MSLConnectionError, match=r"does not accept an indicator-pulse request"):
            device.indicator_pulse()


def test_serial_poll_without_interrupt(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", is_usb_tmc=True, has_intr_read=False)
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.is_488_interface
        usb_backend.add_ctrl_response(b"\x01\x02\x08")  # STATUS_SUCCESS, bTag, status byte
        assert device.serial_poll() == 0x08

        usb_backend.add_ctrl_response(b"\x01\x01\x08")  # STATUS_SUCCESS
        with pytest.raises(MSLConnectionError, match=r"sent bTag \[3\] != received bTag \[1\]"):
            _ = device.serial_poll()

        usb_backend.add_ctrl_response(b"\x01\x02\x04")  # STATUS_SUCCESS, bTag=2
        device._tag_status = 127  # bTag cycles back to 2  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        assert device.serial_poll() == 0x04

        usb_backend.add_ctrl_response(b"\x80\x00\x00")  # STATUS_FAILED
        with pytest.raises(MSLConnectionError, match=r"The request was not successful \[status_code=0x80\]"):
            _ = device.serial_poll()

        device.capabilities.is_488_interface = False
        with pytest.raises(MSLConnectionError, match=r"does not accept a serial-poll request"):
            _ = device.serial_poll()


def test_serial_poll_with_interrupt(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", is_usb_tmc=True, has_intr_read=True)
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.is_488_interface

        usb_backend.add_ctrl_response(b"\x01\x02\x00")  # STATUS_SUCCESS, bTag, reserved
        usb_backend.add_intr_response(bytes([0b00000010, 0]))
        with pytest.raises(MSLConnectionError, match=r"packet, bit 7 is not 1$"):
            _ = device.serial_poll()

        usb_backend.add_ctrl_response(b"\x01\x03\x00")
        usb_backend.add_intr_response(bytes([0b10000001, 0]))
        with pytest.raises(MSLConnectionError, match=r"packet, sent bTag \[3\] != received bTag \[1\]$"):
            _ = device.serial_poll()

        usb_backend.add_ctrl_response(b"\x01\x04\x00")
        usb_backend.add_intr_response(bytes([0b00000000, 0]))
        with pytest.raises(MSLConnectionError, match=r"bit 7 is not 1, sent bTag \[4\] != received bTag \[0\]$"):
            _ = device.serial_poll()

        usb_backend.add_ctrl_response(b"\x01\x05\x00")
        usb_backend.add_intr_response(bytes([0b10000101, 62]))
        assert device.serial_poll() == 62


def test_control_ren(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x", is_usb_tmc=True, has_intr_read=True)
    c = Connection("USB::1::2::x", usb_backend=usb_backend)
    device: USBTMC
    with c.connect() as device:
        for _ in range(100):  # add more than enough STATUS_SUCCESS replies
            usb_backend.add_ctrl_response(b"\x01")

        assert device.capabilities.accepts_remote_local
        for name, value in RENMode.__members__.items():
            device.control_ren(name)
            device.control_ren(value)

        usb_backend.clear_ctrl_response_queue()

        for _ in range(100):  # add more than enough STATUS_FAILED replies
            usb_backend.add_ctrl_response(b"\x80")

        for mode in RENMode:
            with pytest.raises(MSLConnectionError, match=r"The request was not successful \[status_code=0x80\]"):
                device.control_ren(mode)

        usb_backend.clear_ctrl_response_queue()

        device.capabilities.accepts_remote_local = False
        with pytest.raises(MSLConnectionError, match=r"remote-local request"):
            device.control_ren(RENMode.ASSERT)


def test_increment_tag() -> None:
    m = _Message()
    for i in range(1, 256):
        assert i == m.next_tag()
    assert m.next_tag() == 1


def test_dev_dep_msg_out() -> None:
    m = _Message()

    # Example in USBTMC_usb488_subclass_1_00.pdf, Table 3
    assert m.dev_dep_msg_out(b"*IDN?\n") == bytes(
        [0x01, 0x01, 0xFE, 0, 0x06, 0, 0, 0, 0x01, 0, 0, 0, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0x0A, 0, 0]
    )

    # tag increments, eom=False, 2 alignment bytes
    assert m.dev_dep_msg_out(b"*IDN?\n", eom=False) == bytes(
        [0x01, 0x02, 0xFD, 0, 0x06, 0, 0, 0, 0x00, 0, 0, 0, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0x0A, 0, 0]
    )

    # tag increments, 3 alignment bytes
    assert m.dev_dep_msg_out(b"*IDN?", eom=False) == bytes(
        [0x01, 0x03, 0xFC, 0, 0x05, 0, 0, 0, 0x00, 0, 0, 0, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0, 0, 0]
    )

    # tag increments, 1 alignment byte
    assert m.dev_dep_msg_out(b"*IDN?\r\n", eom=False) == bytes(
        [0x01, 0x04, 0xFB, 0, 0x07, 0, 0, 0, 0x00, 0, 0, 0, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0x0D, 0x0A, 0]
    )

    # tag increments, no alignment byte
    assert m.dev_dep_msg_out(b"**IDN?\r\n", eom=False) == bytes(
        [0x01, 0x05, 0xFA, 0, 0x08, 0, 0, 0, 0x00, 0, 0, 0, 0x2A, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0x0D, 0x0A]
    )


def test_request_dev_dep_msg_in() -> None:
    m = _Message()

    # Example in USBTMC_usb488_subclass_1_00.pdf, Table 4
    assert m.request_dev_dep_msg_in(100) == bytes([2, 1, 254, 0, 0x64, 0, 0, 0, 0, 0, 0, 0])

    assert m.request_dev_dep_msg_in(1) == bytes([2, 2, 253, 0, 0x01, 0, 0, 0, 0, 0, 0, 0])
    assert m.request_dev_dep_msg_in(123456789) == bytes([2, 3, 252, 0, 0x15, 0xCD, 0x5B, 0x07, 0, 0, 0, 0])


def test_trigger(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        device.trigger()

        device.capabilities.accepts_trigger = False
        with pytest.raises(MSLConnectionError, match=r"trigger request"):
            device.trigger()

    m = _Message()
    assert m.trigger() == bytes([128, 1, 254, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    assert m.trigger() == bytes([128, 2, 253, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def test_write(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.is_talk_only
        with pytest.raises(MSLConnectionError, match=r"does not accept a write request"):
            _ = device.write(b"hi")

        device.capabilities.is_talk_only = False
        assert device.write_termination == b"\r\n"

        expect = bytes([0x01, 0x01, 0xFE, 0, 0x07, 0, 0, 0, 0x01, 0, 0, 0, 0x2A, 0x49, 0x44, 0x4E, 0x3F, 0x0D, 0x0A, 0])
        assert device.write("*IDN?") == len(expect)

        usb_backend.add_ctrl_response(b"\x80\x00")  # ignore _abort_transfer with (STATUS_FAILED, bTag=0)
        with pytest.raises(MSLConnectionError, match=r"Mocked Bulk-OUT write error"):
            _ = device.write(b"error")


def test_read(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.is_listen_only
        with pytest.raises(MSLConnectionError, match=r"does not accept a read request"):
            _ = device.read()

        device.capabilities.is_listen_only = False

        usb_backend.add_bulk_response(bytes([9, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        usb_backend.add_ctrl_response(b"\x80\x00")  # ignore _abort_transfer with (STATUS_FAILED, bTag=0)
        with pytest.raises(MSLConnectionError, match=r"header, wrong DEV_DEP_MSG_IN value 9 \(expect 2\)$"):
            _ = device.read()

        usb_backend.add_bulk_response(bytes([2, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        usb_backend.add_ctrl_response(b"\x80\x00")  # ignore _abort_transfer with (STATUS_FAILED, bTag=0)
        with pytest.raises(MSLConnectionError, match=r"header, received bTag \[9\] != sent bTag \[2\]$"):
            _ = device.read()

        usb_backend.add_bulk_response(bytes([8, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        usb_backend.add_ctrl_response(b"\x80\x00")  # ignore _abort_transfer with (STATUS_FAILED, bTag=0)
        m = r"header, wrong DEV_DEP_MSG_IN value 8 \(expect 2\), received bTag \[6\] != sent bTag \[3\]$"
        with pytest.raises(MSLConnectionError, match=m):
            _ = device.read()

        # USBTMC_usb488_subclass_1_00.pdf, Table 5 Bulk-IN example
        table_5 = [
            2,
            4,  # index 1: bTag
            0,  # bTag inverse is not considered in reply
            0,
            0x17,  # index 4: transfer size
            0,
            0,
            0,
            0x01,  # index 8: EOM
            0,
            0,
            0,
            0x58,
            0x59,
            0x5A,
            0x43,
            0x4F,
            0x2C,
            0x32,
            0x34,
            0x36,
            0x42,
            0x2C,
            0x53,
            0x2D,
            0x30,
            0x31,
            0x32,
            0x33,
            0x2D,
            0x30,
            0x32,
            0x2C,
            0x30,
            0x0A,
            0x00,
        ]

        usb_backend.add_bulk_response(bytes(table_5))
        assert device.read(decode=False) == b"XYZCO,246B,S-0123-02,0\n"  # cSpell: ignore XYZCO
        assert len(device._byte_buffer) == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        table_5[1] += 1  # increment bTag
        usb_backend.add_bulk_response(bytes(table_5))
        assert device.read(size=10, decode=False) == b"XYZCO,246B"  # cSpell: ignore XYZCO
        assert len(device._byte_buffer) == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        # split into multiple messages
        table_5[1] += 1  # increment bTag
        table_5[4] = 10  # reduce transfer size
        table_5[8] = 0  # not EOM
        usb_backend.add_bulk_response(bytes(table_5)[: 12 + 10])

        table_5[1] += 1  # increment bTag
        table_5[4] = 0x17 - 10  # remaining transfer size
        table_5[8] = 1  # EOM
        remaining = table_5[:12] + table_5[22:]
        usb_backend.add_bulk_response(bytes(remaining))

        assert device.read() == "XYZCO,246B,S-0123-02,0\n"  # cSpell: ignore XYZCO
        assert len(device._byte_buffer) == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        # simulate timeout
        device.timeout = 0.01
        table_5[1] += 1  # increment bTag
        usb_backend.add_bulk_response(bytes(table_5)[:12])
        usb_backend.add_ctrl_response(b"\x80\x00")  # ignore _abort_transfer with (STATUS_FAILED, bTag=0)
        with pytest.raises(MSLTimeoutError):
            _ = device.read()


def test_clear_device_buffers(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        usb_backend.add_ctrl_response(b"\x80")  # STATUS_FAILED for INITIATE_CLEAR
        with pytest.raises(MSLConnectionError, match=r"status_code=0x80"):
            device.clear_device_buffers()

        usb_backend.add_ctrl_response(b"\x01")  # STATUS_SUCCESS for INITIATE_CLEAR
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bmClear=0) for CHECK_CLEAR_STATUS
        device.clear_device_buffers()

        usb_backend.add_ctrl_response(b"\x01")  # STATUS_SUCCESS for INITIATE_CLEAR
        usb_backend.add_ctrl_response(b"\x02\x01")  # (STATUS_PENDING, bmClear=1) for CHECK_CLEAR_STATUS
        usb_backend.add_bulk_response(b"\x00")  # read short packet
        usb_backend.add_ctrl_response(b"\x02\x00")  # (STATUS_PENDING, bmClear=0) for CHECK_CLEAR_STATUS
        # does not read a short packet
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bmClear=0) for CHECK_CLEAR_STATUS

        with caplog.at_level("DEBUG", "msl.equipment"):
            device.clear_device_buffers()

            assert caplog.messages == [
                "USBTMC<||> clearing USBTMC device buffers ...",
                "USBTMC<||>.ctrl_transfer(0xA1, 0x05, 0x0000, 0x0000, 1, 0)",
                "USBTMC<||>.ctrl_transfer(0xA1, 0x06, 0x0000, 0x0000, 2, 0)",
                "USBTMC<||> clearing USBTMC device buffers PENDING [iteration=1]",
                "USBTMC<||>.ctrl_transfer(0xA1, 0x06, 0x0000, 0x0000, 2, 0)",
                "USBTMC<||> clearing USBTMC device buffers PENDING [iteration=2]",
                "USBTMC<||>.ctrl_transfer(0xA1, 0x06, 0x0000, 0x0000, 2, 0)",
                "USBTMC<||>.clear_halt(0x02)",
                "USBTMC<||> clearing USBTMC device buffers done",
            ]


def test_abort_transfer(usb_backend: USBBackend, caplog: pytest.LogCaptureFixture) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    caplog.set_level("DEBUG", "msl.equipment")

    device: USBTMC
    with c.connect() as device:
        abort = device._abort_transfer  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        # CtrlDirection.IN, STATUS_FAILED
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x80\x00")  # (STATUS_FAILED, bTag) for INITIATE_ABORT_BULK
        abort(device.CtrlDirection.IN)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x03, 0x0000, 0x0081, 2, 0)",
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer, INITIATE_ABORT failed [status=0x80]",
        ]

        # CtrlDirection.OUT, STATUS_TRANSFER_NOT_IN_PROGRESS then STATUS_FAILED
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x81\x07")  # (STATUS_TRANSFER_NOT_IN_PROGRESS, bTag) for INITIATE_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x80\x00")  # (STATUS_FAILED, bTag) for INITIATE_ABORT_BULK
        abort(device.CtrlDirection.OUT)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x01, 0x0000, 0x0002, 2, 0)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer, try again with bTag=0x07",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x01, 0x0007, 0x0002, 2, 0)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer, INITIATE_ABORT failed [status=0x80]",
        ]

        # CtrlDirection.IN, without CHECK_ABORT_BULK PENDING
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bTag) for INITIATE_ABORT_BULK
        usb_backend.add_bulk_response(b"\x00")  # read short packet (since aborting a Bulk-IN)
        usb_backend.add_ctrl_response(b"\x80\x00")  # (STATUS_SUCCESS, fifo=0) for CHECK_ABORT_BULK
        abort(device.CtrlDirection.IN)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x03, 0x0000, 0x0081, 2, 0)",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x04, 0x0000, 0x0081, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer done",
        ]

        # CtrlDirection.IN, with CHECK_ABORT_BULK PENDING
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bTag) for INITIATE_ABORT_BULK
        usb_backend.add_bulk_response(b"\x00")  # read short packet (since Bulk-IN)
        usb_backend.add_ctrl_response(b"\x02\x01")  # (STATUS_PENDING, fifo=1) for CHECK_ABORT_BULK
        usb_backend.add_bulk_response(b"\x00")  # read short packet (since Bulk-IN and FIFO=1)
        usb_backend.add_ctrl_response(b"\x02\x00")  # (STATUS_PENDING, fifo=0) for CHECK_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, fifo=0) for CHECK_ABORT_BULK
        abort(device.CtrlDirection.IN)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x03, 0x0000, 0x0081, 2, 0)",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x04, 0x0000, 0x0081, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer PENDING [iteration=1]",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x04, 0x0000, 0x0081, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer PENDING [iteration=2]",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x04, 0x0000, 0x0081, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.IN: 128> transfer done",
        ]

        # CtrlDirection.OUT, without CHECK_ABORT_BULK PENDING
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bTag) for INITIATE_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x80\x00")  # (STATUS_SUCCESS, fifo=0) for CHECK_ABORT_BULK
        abort(device.CtrlDirection.OUT)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x01, 0x0000, 0x0002, 2, 0)",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x02, 0x0000, 0x0002, 8, 0)",
            "USBTMC<||>.clear_halt(0x02)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer done",
        ]

        # CtrlDirection.OUT, with CHECK_ABORT_BULK PENDING
        caplog.clear()
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, bTag) for INITIATE_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x02\x00")  # (STATUS_PENDING, fifo=0) for CHECK_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x02\x00")  # (STATUS_PENDING, fifo=0) for CHECK_ABORT_BULK
        usb_backend.add_ctrl_response(b"\x01\x00")  # (STATUS_SUCCESS, fifo=0) for CHECK_ABORT_BULK
        abort(device.CtrlDirection.OUT)
        assert caplog.messages == [
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer ...",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x01, 0x0000, 0x0002, 2, 0)",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x02, 0x0000, 0x0002, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer PENDING [iteration=1]",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x02, 0x0000, 0x0002, 8, 0)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer PENDING [iteration=2]",
            "USBTMC<||>.ctrl_transfer(0xA2, 0x02, 0x0000, 0x0002, 8, 0)",
            "USBTMC<||>.clear_halt(0x02)",
            "USBTMC<||> aborting <CtrlDirection.OUT: 0> transfer done",
        ]
