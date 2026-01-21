from __future__ import annotations

from array import array
from typing import TYPE_CHECKING

import pytest

from msl.equipment import USB, USBTMC, Connection, MSLConnectionError
from msl.equipment.interfaces.usbtmc import _Capabilities  # pyright: ignore[reportPrivateUsage]

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


def test_usbtmc_not_found() -> None:
    c = Connection("USB::0x2a2b::0x1122::ABC123")
    with pytest.raises(MSLConnectionError, match=r"The USB device was not found"):
        _ = c.connect()


def test_capabilities() -> None:  # noqa: PLR0915
    response = array("B", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    c = _Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert not c.accepts_remote_local
    assert not c.accepts_service_request
    assert not c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_full_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 0, 0, 0, 0, 0, 0, 0, 0])
    c = _Capabilities(response)
    assert c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_full_488
    assert c.is_listen_only
    assert c.is_talk_only

    response[0] = 0  # simulate an unsuccessful response
    c = _Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert not c.accepts_remote_local
    assert not c.accepts_service_request
    assert not c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_full_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 6, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = _Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert not c.accepts_term_char
    assert c.accepts_trigger  # is_dt_capable=True OR accepts_interface_trigger=False  => True
    assert c.is_full_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    response = array("B", [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 7, 15, 0, 0, 0, 0, 0, 0, 0, 0])
    c = _Capabilities(response)
    assert not c.accepts_indicator_pulse
    assert c.accepts_remote_local
    assert c.accepts_service_request
    assert c.accepts_term_char
    assert c.accepts_trigger
    assert c.is_full_488
    assert not c.is_listen_only
    assert not c.is_talk_only

    # enable: indicator pulse, listen only, term char, REN_CONTROL, SR1
    data = [1, 0, 0, 0, 0b00000101, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0b00000010, 0b00000100, 0, 0, 0, 0, 0, 0, 0, 0]
    response = array("B", data)
    c = _Capabilities(response)
    assert c.accepts_indicator_pulse
    assert c.accepts_remote_local  # because of REN_CONTROL
    assert c.accepts_service_request  # because SR1
    assert c.accepts_term_char
    assert not c.accepts_trigger
    assert not c.is_full_488
    assert c.is_listen_only
    assert not c.is_talk_only
