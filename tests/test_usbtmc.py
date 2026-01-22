from __future__ import annotations

import sys
from array import array
from typing import TYPE_CHECKING

import pytest

from msl.equipment import USB, USBTMC, Connection, MSLConnectionError
from msl.equipment.interfaces.usbtmc import Capabilities

if TYPE_CHECKING:
    from tests.conftest import USBBackend


NO_LIBUSB1 = sys.platform == "darwin" and sys.version_info[:2] == (3, 8)


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


@pytest.mark.skipif(NO_LIBUSB1, reason="libusb1 not available in CI")
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
    assert not c.is_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_488
    assert c.is_listen_only
    assert c.is_talk_only

    response[0] = 0  # simulate an unsuccessful response
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert not c.accepts_remote_local
    assert not c.accepts_service_request
    assert not c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 6, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert not c.accepts_term_char
    assert c.accepts_trigger  # is_dt_capable=True OR accepts_interface_trigger=False  => True
    assert c.is_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 7, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_488
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
    assert not c.is_488
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
        "  is_488=False,\n"
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
        with pytest.raises(MSLConnectionError, match=r"does not accept the indicator-pulse request"):
            device.indicator_pulse()


def test_serial_poll(usb_backend: USBBackend) -> None:
    usb_backend.add_device(1, 2, "x")
    c = Connection("USB::1::2::x", usb_backend=usb_backend)

    device: USBTMC
    with c.connect() as device:
        assert device.capabilities.is_488
        usb_backend.add_ctrl_response(b"\x01\x02\x08")  # STATUS_SUCCESS, bTag, status byte
        assert device.serial_poll() == 0x08

        usb_backend.add_ctrl_response(b"\x01\x01\x08")  # STATUS_SUCCESS
        with pytest.raises(MSLConnectionError, match=r"sent bTag \[3\] != received bTag \[1\]"):
            _ = device.serial_poll()

        usb_backend.add_ctrl_response(b"\x01\x02\x04")  # STATUS_SUCCESS, bTag=2
        device._status_tag = 127  # bTag cycles back to 2  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        assert device.serial_poll() == 0x04

        usb_backend.add_ctrl_response(b"\x80\x00\x00")  # STATUS_FAILED
        with pytest.raises(MSLConnectionError, match=r"The request was not successful \[status_code=0x80\]"):
            _ = device.serial_poll()

        device.capabilities.is_488 = False
        with pytest.raises(MSLConnectionError, match=r"does not accept the serial-poll request"):
            _ = device.serial_poll()
