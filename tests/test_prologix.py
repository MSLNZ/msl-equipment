from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import pytest

from msl.equipment import Connection, Equipment, MessageBased, MSLConnectionError, Prologix
from msl.equipment.interfaces import MSLTimeoutError
from msl.equipment.interfaces.prologix import find_prologix, parse_prologix_address

if TYPE_CHECKING:
    from tests.conftest import TCPServer


@pytest.mark.parametrize(
    "address",
    [
        "",
        "Prologix",
        "Prologix::",
        "Prologix::COM2",
        "Prologic::COM2::6",  # cSpell: ignore Prologic
        "COM6",
        "SDK::filename.dll",
        "SOCKET::1.2.3.4::1234",
        "Prologix::COM 2::20",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_prologix_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("Prologix::COM1::1", (0, "COM1", 1, None)),  # (ethernet, hw_address, pad, sad)
        ("Prologix::COM2::2::96", (0, "COM2", 2, 96)),
        ("Prologix::COM3::GPIB::11", (0, "COM3", 11, None)),
        ("Prologix::COM4::GPIB0::7", (0, "COM4", 7, None)),
        ("Prologix::COM5::GPIB1::25::96", (0, "COM5", 25, 96)),
        ("Prologix::/dev/ttyS0::20", (0, "/dev/ttyS0", 20, None)),
        ("Prologix::/dev/ttyS1::20::115", (0, "/dev/ttyS1", 20, 115)),
        ("Prologix::/dev/ttyS2::GPIB::3", (0, "/dev/ttyS2", 3, None)),
        ("Prologix::/dev/ttyS3::GPIB0::11", (0, "/dev/ttyS3", 11, None)),
        ("Prologix::/dev/ttyS0::GPIB2::10::100", (0, "/dev/ttyS0", 10, 100)),
        ("Prologix::192.168.1.100::1234::12", (1234, "192.168.1.100", 12, None)),
        ("Prologix::192.168.1.100::1234::1::96", (1234, "192.168.1.100", 1, 96)),
        ("Prologix::192.168.1.100::12345::GPIB::1", (12345, "192.168.1.100", 1, None)),
        ("Prologix::192.168.1.100::52421::GPIB0::22", (52421, "192.168.1.100", 22, None)),
        ("Prologix::192.168.1.100::1234::GPIB1::17::117", (1234, "192.168.1.100", 17, 117)),
        ("Prologix::domainname::1234::4", (1234, "domainname", 4, None)),
        ("Prologix::domainname::1234::1::96", (1234, "domainname", 1, 96)),
        ("Prologix::dom.ain.name::1234::GPIB::1", (1234, "dom.ain.name", 1, None)),
        ("Prologix::prologix-00-01-02-03-04-05::1234::GPIB0::2", (1234, "prologix-00-01-02-03-04-05", 2, None)),
        ("Prologix::dom.ain.name::1234::GPIB1::3::121", (1234, "dom.ain.name", 3, 121)),
        ("Prologix::/dev/pts/1::1", (0, "/dev/pts/1", 1, None)),
        ("PROLOGIX::/dev/ttyS1::16::100", (0, "/dev/ttyS1", 16, 100)),
        ("ProLOgiX::/dev/ttyS0::16::96", (0, "/dev/ttyS0", 16, 96)),
    ],
)
def test_parse_address_valid(address: str, expected: tuple[bool, str, int, int | None]) -> None:
    parsed = parse_prologix_address(address)
    enet_port, hw_address, pad, sad = expected
    assert parsed is not None
    assert parsed.enet_port == enet_port
    assert parsed.hw_address == hw_address
    assert parsed.pad == pad
    assert parsed.sad == sad


def test_connection_message_based_attributes() -> None:
    # Prologix must have the same public attributes as MessageBased
    dir_p = dir(Prologix)
    dir_mb = dir(MessageBased)

    for attr in dir_mb:
        if attr.startswith("_"):
            continue
        assert attr in dir_p

    ignore = {
        "clear",
        "controller",
        "group_execute_trigger",
        "interface_clear",
        "local",
        "local_lockout",
        "prologix_help",
        "query_auto",
        "serial_poll",
        "set_status_byte",
        "trigger",
        "wait_for_srq",
    }
    for attr in dir_p:
        if attr.startswith("_") or attr in ignore:
            continue
        assert attr in dir_mb


def test_find_prologix(tcp_server: type[TCPServer]) -> None:
    description = "Prologix GPIB-ETHERNET Controller version 01.06.06.00"
    with tcp_server() as server:
        server.add_response(description.encode() + b"\n")
        devices = find_prologix(ip=[server.host], port=server.port, timeout=0.2)
        assert devices
        for ipv4, device in devices.items():
            assert isinstance(ipv4, str)
            assert device.description.startswith(description)
            for address in device.addresses:
                assert address == f"Prologix::{server.host}::{server.port}::GPIB::<PAD>[::<SAD>]"


def test_find_prologix_unknown_response(tcp_server: type[TCPServer]) -> None:
    with tcp_server() as server:
        server.add_response(b"Does not start with 'Prologix'\n")
        devices = find_prologix(ip=[server.host], port=server.port, timeout=0.2)
        assert devices == {}


def test_find_prologix_no_device() -> None:
    assert find_prologix(ip=["127.0.0.1"], timeout=0.1) == {}


def test_connect_invalid_pad() -> None:
    c = Connection("Prologix::Whatever::50")
    with pytest.raises(ValueError, match=r"Invalid primary GPIB address 50"):
        _ = c.connect()


def test_connect_invalid_sad() -> None:
    c = Connection("Prologix::Whatever::10::50")
    with pytest.raises(ValueError, match=r"Invalid secondary GPIB address 50"):
        _ = c.connect()


def test_connect_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid Prologix address"):
        _ = Prologix(Equipment(connection=Connection("COM1")))


def test_connect_invalid_port() -> None:
    c = Connection("Prologix::COM254::6")
    with pytest.raises(MSLConnectionError, match=r"could not open port"):
        _ = c.connect()


def test_socket(tcp_server: type[TCPServer]) -> None:  # noqa: PLR0915
    term = b"\n"
    with tcp_server(term=term) as server:
        c = Connection(
            f"Prologix::{server.host}::{server.port}::6",
            timeout=1,
            read_tmo_ms=1000,
            eot_char=13,
        )
        pro: Prologix = c.connect()
        try:
            assert not pro.rstrip
            pro.rstrip = False
            assert not pro.rstrip
            assert not pro.controller.rstrip
            pro.read_termination = term
            assert pro.read_termination == term
            assert pro.controller.read_termination == term
            pro.write_termination = term
            assert pro.write_termination == term
            assert pro.controller.write_termination == term
            pro.encoding = "ascii"
            assert pro.encoding == "ascii"
            assert pro.controller.encoding == "ascii"
            pro.timeout = 0.9
            assert pro.timeout == 0.9
            assert pro.controller.timeout == 0.9
            pro.max_read_size = 1024
            assert pro.max_read_size == 1024
            assert pro.controller.max_read_size == 1024
            assert hasattr(pro.controller, "socket")

            assert pro.read() == "++mode 1\r\n"
            assert pro.read() == "++eoi 1\r\n"
            assert pro.read() == "++eos 3\r\n"
            assert pro.read() == "++eot_char 13\r\n"
            assert pro.read() == "++eot_enable 1\r\n"
            assert pro.read() == "++read_tmo_ms 1000\r\n"
            assert pro.read() == "++addr 6\r\n"

            for _ in range(7):  # clear the write("++read 10") that is written in the 7 pro.read()'s above
                assert pro.controller.read() == "++read 10\n"

            assert pro.query_auto
            assert pro.query("AUTO") == "++auto 1\n"
            assert pro.read() == "AUTO\n"
            assert pro.read() == "++auto 0\n"

            for _ in range(2):  # clear the write("++read 10") that is written in the 2 pro.read()'s above
                assert pro.controller.read() == "++read 10\n"

            server.add_response(b"The following commands are available:\n")
            server.add_response(b"++help -- description\n")
            reply = pro.prologix_help()
            assert reply == [("++help", "description")]
            with contextlib.suppress(MSLTimeoutError):  # flaky assert
                assert pro.controller.read() == "++auto 0\n"  # leftover from pro.query() inside pro.prologix_help()

            pro.query_auto = False
            assert pro.query("foo", delay=0.05) == "foo\n"

            pro.group_execute_trigger()
            assert pro.read() == "++trg\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            pro.group_execute_trigger(1, 2, 3)
            assert pro.read() == "++trg 1 2 3\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            pro.clear()
            assert pro.read() == "++clr\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            pro.interface_clear()
            assert pro.read() == "++ifc\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            pro.local()
            assert pro.read() == "++loc\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            pro.local_lockout()
            assert pro.read() == "++llo\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            server.add_response(b"32\n")
            assert pro.serial_poll() == 32

            pro.set_status_byte(16)
            assert pro.read() == "++status 16\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            for value in [-1, 256]:
                with pytest.raises(ValueError, match=r"must be in range"):
                    pro.set_status_byte(value)

            pro.trigger()
            assert pro.read() == "++trg 6\n"
            assert pro.controller.read() == "++read 10\n"  # clear the write("++read 10") that is written in pro.read()

            server.add_response(b"0\n")
            server.add_response(b"0\n")
            server.add_response(b"0\n")
            server.add_response(b"1\n")
            pro.wait_for_srq()
            server.clear_response_queue()

            server.add_response(b"0\n")
            server.add_response(b"0\n")
            server.add_response(b"0\n")
            with pytest.raises(TimeoutError, match=r"0.1 seconds"):
                pro.wait_for_srq(timeout=0.1)
            server.clear_response_queue()

            pro.read_termination = None  # force EOI
            pro.trigger()
            assert pro.read(size=8) == "++trg 6\n"
            assert pro.controller.read(size=11) == "++read eoi\n"  # eoi

        finally:
            _ = pro.write(b"SHUTDOWN")

        pro.disconnect()
        with pytest.raises(MSLConnectionError, match=r"Disconnected from Prologix GPIB device"):
            _ = pro.read()


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = Prologix(Equipment())
