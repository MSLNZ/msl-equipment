from __future__ import annotations

import socket
import sys
import threading
import time

import pytest
from msl.loadlib.utils import get_available_port

from msl.equipment import Connection, Equipment, HiSLIP, MSLConnectionError, MSLTimeoutError
from msl.equipment.interfaces.hislip import PORT, AsyncInitialize, Message, parse_hislip_address

IS_WINDOWS = sys.platform == "win32"


def server(address: str, port: int, action: str) -> None:
    # Simulate a HiSLIP server.

    # The payloads for the request/reply were determined when an instrument
    # was on the same network as the computer. The client did the following:
    # 1. Synchronous channel connects
    # 2. Initialize request
    # 3. Asynchronous channel connects
    # 4. AsyncInitialize request
    # 5. AsyncMaximumMessageSize request
    # 6. "*IDN?" query (synchronous channel)

    initialize_request = b"HS\x00\x00\x01\x00XX\x00\x00\x00\x00\x00\x00\x00\x07hislip0"

    initialize_response = b"HS\x01\x00\x01\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00"

    async_initialize_request = b"HS\x11\x00\x00\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00"

    async_initialize_response = b"HS\x12\x00\x00\x00XX\x00\x00\x00\x00\x00\x00\x00\x00"

    async_maximum_message_size_request = (
        b"HS\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x10\x00\x00"
    )

    async_maximum_message_size_response = (
        b"HS\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x10\x00\x00"
    )

    idn_request = b"HS\x07\x00\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x05*IDN?"

    idn_reply = (
        b"HS\x07\x00\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00H"
        b"Manufacturer of the Device,Model,Serial,X.01.23-45.67-89.ab-cd.ef-gh-ij\n"
        b"\x00\x00\x00\x00\x00\x00"
    )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((address, port))
    s.listen(2)
    sync_conn, _ = s.accept()  # synchronous channel connects
    data = sync_conn.recv(256)
    if not data:
        sync_conn.close()
        s.close()
        return

    assert data == initialize_request
    sync_conn.sendall(initialize_response)
    async_conn, _ = s.accept()  # asynchronous channel connects
    data = async_conn.recv(256)
    assert data == async_initialize_request
    async_conn.sendall(async_initialize_response)
    data = async_conn.recv(256)
    assert data == async_maximum_message_size_request
    async_conn.sendall(async_maximum_message_size_response)
    data = sync_conn.recv(256)
    if action == "idn":
        assert data == idn_request
        sync_conn.sendall(idn_reply)
    elif action == "sleep":
        time.sleep(1.5)  # must be > 1
    elif action == "bad-header":
        sync_conn.sendall(b"<16bytes")
    while True:
        # wait for asynchronous channel to disconnect
        # it disconnects before the synchronous channel
        data = async_conn.recv(256)
        if not data:
            break
    sync_conn.close()
    async_conn.close()
    s.close()


@pytest.mark.parametrize(
    "address",
    [
        "TCPIP::dev.company.com::INSTR",
        "GPIB::23",
        "TCPIP::dev.company.com::hislip",
        "TCPIP0::dev.company.com::instr::INSTR",
        "TCPIP0::10.0.0.1::usb0[1234::5678::SERIAL::0]::INSTR",
        "TCPIP::1.1.1.1::gpib,5::INSTR",
        "TCPIP::1.1.1.1::gpib,5",
        "TCPIP0::company::hislip0,port::INSTR",
        "tcpip3::10.0.0.1::USB0::instr",
        "TCP::myMachine::1234",
        "TCPIP0::testMachine1::COM1,488::INSTR",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_hislip_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("TCPIP::1.2.3.4::HiSLIP0::INSTR", (0, "1.2.3.4", "HiSLIP0", PORT)),
        ("TCPIP::company::hislip1,3::INSTR", (0, "company", "hislip1", 3)),
        ("tcpip::company::hislip1,30000::INSTR", (0, "company", "hislip1", 30000)),
        ("TCPIP0::1.2.3.4::hislip0", (0, "1.2.3.4", "hislip0", PORT)),
        ("TCPIP1::company::hislip0,4880::INSTR", (1, "company", "hislip0", 4880)),
        ("TCPIP2::192.168.1.100::hislip10,30000::INSTR", (2, "192.168.1.100", "hislip10", 30000)),
    ],
)
def test_parse_address_valid(address: str, expected: tuple[int, str, str, int]) -> None:
    parsed = parse_hislip_address(address)
    board, host, name, port = expected
    assert parsed is not None
    assert parsed.board == board
    assert parsed.host == host
    assert parsed.name == name
    assert parsed.port == port


def test_protocol() -> None:
    address = "127.0.0.1"
    port = get_available_port()

    t = threading.Thread(target=server, args=(address, port, "idn"))
    t.daemon = True
    t.start()
    time.sleep(0.1)  # allow some time for the server to start

    connection = Connection(f"TCPIP::{address}::hislip0,{port}", timeout=1)

    dev: HiSLIP = connection.connect()
    assert dev.timeout == 1
    assert dev.asynchronous.get_timeout() == 1
    assert dev.synchronous.get_timeout() == 1
    assert dev.lock_timeout == 0
    assert dev.read_termination is None
    assert dev.write_termination is None
    assert dev.query("*IDN?") == "Manufacturer of the Device,Model,Serial,X.01.23-45.67-89.ab-cd.ef-gh-ij\n"

    dev.timeout = -1
    assert dev.timeout is None
    assert dev.asynchronous.get_timeout() is None  # type: ignore[unreachable]
    assert dev.synchronous.get_timeout() is None

    dev.timeout = 0
    assert dev.timeout == 0.0
    assert dev.asynchronous.get_timeout() == 0.0
    assert dev.synchronous.get_timeout() == 0.0

    dev.timeout = None
    assert dev.timeout is None
    assert dev.asynchronous.get_timeout() is None
    assert dev.synchronous.get_timeout() is None

    dev.timeout = 1.1
    assert dev.timeout == 1.1
    assert dev.asynchronous.get_timeout() == 1.1
    assert dev.synchronous.get_timeout() == 1.1

    dev.lock_timeout = -2.1
    assert dev.lock_timeout == 0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = None
    assert dev.lock_timeout == 0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = 0
    assert dev.lock_timeout == 0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = 1.2
    assert dev.lock_timeout == 1.2
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.disconnect()

    assert dev.asynchronous.socket is None
    assert dev.synchronous.socket is None


def test_exceptions() -> None:
    address = "127.0.0.1"

    # server not running
    port = get_available_port()
    connection = Connection(f"TCPIP0::{address}::hislip0,{port}::INSTR", timeout=1, rstrip=True)

    error = MSLTimeoutError if IS_WINDOWS else MSLConnectionError
    with pytest.raises(error):
        _ = connection.connect()

    # server hangs during a query (after the connection is established)
    port = get_available_port()
    connection = Connection(f"TCPIP0::{address}::hislip0,{port}::INSTR", timeout=1, rstrip=True)

    t = threading.Thread(target=server, args=(address, port, "sleep"), daemon=True)
    t.start()
    time.sleep(0.1)  # allow some time for the server to start

    dev: HiSLIP = connection.connect()
    with pytest.raises(MSLTimeoutError, match=r"Timeout occurred after 1.0 second\(s\)"):
        _ = dev.query("sleep")
    t.join()

    # server returns a bad header (after the connection is established)
    port = get_available_port()
    connection = Connection(f"TCPIP0::{address}::hislip0,{port}::INSTR", timeout=1, rstrip=True)

    t = threading.Thread(target=server, args=(address, port, "bad-header"))
    t.daemon = True
    t.start()
    time.sleep(0.1)  # allow some time for the server to start
    dev = connection.connect()
    with pytest.raises(MSLConnectionError, match=r"The reply header is != 16 bytes"):
        _ = dev.query("bad-header")
    t.join()


def test_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid HiSLIP address"):
        _ = HiSLIP(Equipment(connection=Connection("COM2")))


def test_message_as_string() -> None:
    assert str(Message()) == "Message(type=UNDEFINED, control_code=0, parameter=0, payload=b'')"
    assert repr(Message()) == "Message(type=UNDEFINED, control_code=0, parameter=0, payload=b'')"

    msg = AsyncInitialize(4, 3, b"x" * 25)
    assert (
        str(msg) == "Message(type=AsyncInitialize, control_code=4, parameter=3, payload=b'xxxxxxxxxxxxxxxxxxxxxxxxx')"
    )

    msg = AsyncInitialize(payload=b"abcdefghijklmnopqrstuvwxyz" * 4)
    assert (
        str(msg)
        == "Message(type=AsyncInitialize, control_code=0, parameter=0, payload[len=104]=b'abcdefghijklmnopqrstuvwxy'...b'bcdefghijklmnopqrstuvwxyz')"  # cSpell: ignore bcdefghijklmnopqrstuvwxyz  # noqa: E501
    )
