from __future__ import annotations

import struct
import sys
from typing import TYPE_CHECKING

import pytest

from msl.equipment import Connection, Equipment, MSLConnectionError, MSLTimeoutError
from msl.equipment.interfaces import vxi11
from msl.equipment.interfaces.vxi11 import VXI11, AcceptStatus, AuthStatus, MessageType, RejectStatus, ReplyStatus

if TYPE_CHECKING:
    from tests.conftest import TCPServer


IS_WINDOWS = sys.platform == "win32"


@pytest.mark.parametrize(
    "address",
    [
        "TCP::dev.company.com::INSTR",
        "GPIB::23",
        "TCPIP::dev.company.com::hislip::INSTR",
        "TCPIP::1.2.3.4::HiSLIP0::INSTR",
        "TCPIP::company::hislip1,3::INSTR",
        "TCPIP0::192.168.2.100::hislip0",
        "TCPIP0::dev.company.com::instr::INSTR",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert vxi11.parse_vxi_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("TCPIP::dev.company.com::InStR", (0, "dev.company.com", "inst0")),
        ("TCPIP1::company::INSTR", (1, "company", "inst0")),
        ("TCPIP0::10.0.0.1::usb0[1234::5678::SERIAL::0]::INSTR", (0, "10.0.0.1", "usb0[1234::5678::SERIAL::0]")),
        ("TCPIP::10.0.0.1::usb0[1234::5678::SERIAL::0]", (0, "10.0.0.1", "usb0[1234::5678::SERIAL::0]")),
        (
            "TCPIP0::myMachine::usb0[2391::1031::SN_00123::0]::INSTR",
            (0, "myMachine", "usb0[2391::1031::SN_00123::0]"),
        ),
        ("TCPIP::10.0.0.1::instr2::INSTR", (0, "10.0.0.1", "instr2")),
        ("TCPIP2::10.0.0.1::instr1", (2, "10.0.0.1", "instr1")),
        ("TCPIP::1.1.1.1::gpib,5::INSTR", (0, "1.1.1.1", "gpib,5")),
        ("TCPIP10::192.168.1.100::gpib,5::iNsTr", (10, "192.168.1.100", "gpib,5")),
        ("tcpip3::10.0.0.1::USB0::instr", (3, "10.0.0.1", "USB0")),
        ("TCPIP0::123.456.0.21::gpib0,2,3", (0, "123.456.0.21", "gpib0,2,3")),
        ("TCPIP0::myMachine::inst0::INSTR", (0, "myMachine", "inst0")),
        ("TCPIP::myMachine", (0, "myMachine", "inst0")),
        ("TCPIP0::testMachine1::COM1,488::INSTR", (0, "testMachine1", "COM1,488")),
        ("TCPIP0::myMachine::gpib0,2", (0, "myMachine", "gpib0,2")),
        ("TCPIP0::myMachine::UsbDevice1::INSTR", (0, "myMachine", "UsbDevice1")),
    ],
)
def test_parse_address_valid(address: str, expected: tuple[int, str, str]) -> None:
    board, host, name = expected
    info = vxi11.parse_vxi_address(address)
    assert info is not None
    assert info.board == board
    assert info.host == host
    assert info.name == name


def test_find_vxi11() -> None:
    for ipv4, device in vxi11.find_vxi11().items():
        assert isinstance(ipv4, str)
        assert device.description
        assert device.webserver
        for address in device.addresses:
            assert address.startswith("TCPIP::")
            assert address.endswith(("::inst0::INSTR", "::SOCKET", "::hislip0::INSTR"))


def test_rpc_client() -> None:
    client = vxi11.RPCClient("")
    assert client.chunk_size == 4096
    client.chunk_size = 1024
    assert client.chunk_size == 1024

    assert client.get_buffer() == bytearray()
    client.append(b"abc")
    client.append_opaque("hello")  # \x00 padded 3 times (8-5=3)
    client.append_opaque(b"")  # empty input, so ignored
    client.append_opaque(b"xxxx")  # multiple of 4, no padding
    client.append_opaque(memoryview(b"foo"))  # \x00 padded once
    assert client.get_buffer() == bytearray(
        b"abc\x00\x00\x00\x05hello\x00\x00\x00\x00\x00\x00\x04xxxx\x00\x00\x00\x03foo\x00"
    )

    assert client.unpack_opaque(b"") == b""
    assert client.unpack_opaque(b"\x00\x00\x00\x05hello\x00\x00\x00") == b"hello"
    assert client.unpack_opaque(b"\x00\x00\x00\x04xxxx") == b"xxxx"
    assert client.unpack_opaque(b"\x00\x00\x00\x03foo\x00") == b"foo"

    # the transaction identifier is 0 until client.init() is called
    assert client._xid == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    xid = 0

    # wrong xid
    msg = struct.pack(">2I", xid + 1, MessageType.REPLY)
    assert client.check_reply(memoryview(msg)) is None

    # message type is not REPLY
    msg = struct.pack(">2I", xid, MessageType.CALL)
    with pytest.raises(RuntimeError, match=r"RPC message type is not <MessageType.REPLY: 1>, got 0"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> Unknown ReplyStatus
    msg = struct.pack(">3I", xid, MessageType.REPLY, 9999)
    with pytest.raises(RuntimeError, match=r"RPC reply is not MSG_ACCEPTED nor MSG_DENIED"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_DENIED -> RPC_MISMATCH (low: 1, high: 2)
    msg = struct.pack(">6I", xid, MessageType.REPLY, ReplyStatus.MSG_DENIED, RejectStatus.RPC_MISMATCH, 1, 2)
    with pytest.raises(RuntimeError, match=r"RPC call failed: <RejectStatus.RPC_MISMATCH: 0>: low=1, high=2"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_DENIED -> AUTH_ERROR -> AUTH_BADCRED
    msg = struct.pack(
        ">5I", xid, MessageType.REPLY, ReplyStatus.MSG_DENIED, RejectStatus.AUTH_ERROR, AuthStatus.AUTH_BADCRED
    )
    with pytest.raises(RuntimeError, match=r"RPC authentication failed: <AuthStatus.AUTH_BADCRED: 1>"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_DENIED -> Unknown RejectStatus
    msg = struct.pack(">4I", xid, MessageType.REPLY, ReplyStatus.MSG_DENIED, 9999)
    with pytest.raises(RuntimeError, match=r"RPC MSG_DENIED reply status is not RPC_MISMATCH nor AUTH_ERROR"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_ACCEPTED -> PROG_MISMATCH (low: 3, high: 4)
    msg = (
        struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)
        + struct.pack(">QI", 0, AcceptStatus.PROG_MISMATCH)  # verify=0 (since VXI-11 does not use authentication)
        + struct.pack(">2I", 3, 4)
    )
    with pytest.raises(RuntimeError, match=r"RPC call failed: <AcceptStatus.PROG_MISMATCH: 2>: low=3, high=4"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_ACCEPTED -> PROG_MISMATCH (low: 3, high: 4)
    msg = (
        struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)
        + struct.pack(">QI", 0, AcceptStatus.PROC_UNAVAIL)  # verify=0 (since VXI-11 does not use authentication)
    )
    with pytest.raises(RuntimeError, match=r"RPC call failed: <AcceptStatus.PROC_UNAVAIL: 3>"):
        _ = client.check_reply(memoryview(msg))

    # REPLY -> MSG_ACCEPTED -> SUCCESS
    msg = (
        struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # verify=0 (since VXI-11 does not use authentication)
        + b"foo"  # message
    )
    reply = client.check_reply(memoryview(msg))
    assert reply is not None
    assert reply.tobytes() == b"foo"


def test_rpc_client_connect(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"\x00") as server:
        client = vxi11.RPCClient(server.host)
        try:
            assert client.socket is None
            client.connect(server.port, timeout=1)
            assert client.socket is not None

            assert client.socket.gettimeout() == 1  # type: ignore[unreachable]
            client.set_timeout(0.9)
            assert client.socket.gettimeout() == 0.9

            # transaction identifier gets incremented
            assert client._xid == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            client.init(10, 11, 12)
            assert client._xid == 1  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            xid = 1

            assert client.get_buffer() == (
                struct.pack(">2I", xid, MessageType.CALL)
                + struct.pack(">4I2Q", 2, 10, 11, 12, 0, 0)  # RFC 1057 (page 10): struct call_body
            )

            server.add_response(b"a")  # < 4 bytes
            client.write()  # write whatever is in the buffer to get the response that was added to the queue
            with pytest.raises(EOFError):
                _ = client.read()

            msg = (
                b"\x80\x00\x00 "  # last fragment, fragment size is 32 bytes (a SPACE in ASCII is 32)
                + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
                + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
                + b"abcdefgh"  # 8 more bytes to complete fragment size
            )
            server.add_response(msg)
            client.write()  # write whatever is in the buffer to get the response that was added to the queue
            assert client.read().tobytes() == b"abcdefgh"

        finally:
            client.close()

        assert client.socket is None  # type: ignore[unreachable]
        with pytest.raises(RuntimeError, match=r"socket is disconnected"):
            client.set_timeout(1.1)


def test_port_mapper(tcp_server: type[TCPServer]) -> None:
    rpc_server = tcp_server(term=None)
    rpc_server.start()

    vxi11.PMAP_PORT = rpc_server.port

    rpc_program = tcp_server(term=None)
    rpc_program.start()

    timeout = 1
    connection = Connection(f"TCPIP::{rpc_server.host}", timeout=timeout)

    xid = 1  # first transaction sent to rpc_server to get the port that rpc_program is running on
    msg = (
        b"\x80\x00\x00\x1c"  # last fragment, fragment size is 28 bytes \x1c
        + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">I", rpc_program.port)  # 4 bytes
    )
    rpc_server.add_response(msg)

    xid = 1  # first transaction sent to rpc_program to request a link ID
    vxi_error_code = 0
    link_id = 1
    abort_port = 619
    max_recv_size = 1024

    # create_link() response
    msg = (
        b"\x80\x00\x00("  # fragment size is 40 bytes, ( is ASCII 40
        + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">4L", vxi_error_code, link_id, abort_port, max_recv_size)  # 16 bytes
    )
    rpc_program.add_response(msg)

    # destroy_link() response
    msg = (
        b"\x80\x00\x00\x1c"  # last fragment, fragment size is 28 bytes \x1c
        + struct.pack(">3I", xid + 1, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">L", vxi_error_code)  # 4 bytes
    )
    rpc_program.add_response(msg)

    dev: VXI11 = connection.connect()
    assert dev._link_id == link_id  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._abort_port == abort_port  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._max_recv_size == max_recv_size  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    dev.disconnect()

    rpc_server.stop()
    rpc_program.stop()


def test_timeout(tcp_server: type[TCPServer]) -> None:  # noqa: PLR0915
    rpc_program = tcp_server(term=None)
    rpc_program.start()

    timeout = 1
    connection = Connection(f"TCPIP::{rpc_program.host}", timeout=timeout, port=rpc_program.port)

    xid = 1  # first transaction sent to rpc_program to request a link ID
    vxi_error_code = 0
    link_id = 1
    abort_port = 619
    max_recv_size = 1024

    # create_link() response
    msg = (
        b"\x80\x00\x00("  # fragment size is 40 bytes, ( is ASCII 40
        + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">4L", vxi_error_code, link_id, abort_port, max_recv_size)  # 16 bytes
    )
    rpc_program.add_response(msg)

    # number of bytes received from write(), this won't have the correct bytes,
    # so an MSLTimeoutError error will be raised
    msg = (
        b"\x80\x00\x00\\"  # fragment size is 92 bytes, \ is ASCII 92
        + struct.pack(">3I", xid + 1, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">L", vxi_error_code)  # 4 bytes
        + b"not 92 bytes"
    )
    rpc_program.add_response(msg)

    # destroy_link() response
    msg = (
        b"\x80\x00\x00\x1c"  # last fragment, fragment size is 28 bytes \x1c
        + struct.pack(">3I", xid + 2, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">L", vxi_error_code)  # 4 bytes
    )
    rpc_program.add_response(msg)

    dev: VXI11 = connection.connect()

    assert dev.socket is not None

    # 1 day is considered equivalent to blocking mode
    blocking_timeout_ms = int(vxi11.ONE_DAY * 1000)

    dev.timeout = -1
    assert dev._timeout is None  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._io_timeout_ms == blocking_timeout_ms  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() is None

    dev.timeout = 0
    assert dev._timeout == 0.0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._io_timeout_ms == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 0.0 + 0.0  # 1 + io_timeout + lock_timeout

    dev.timeout = None
    assert dev._timeout is None  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._io_timeout_ms == blocking_timeout_ms  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() is None

    dev.timeout = 1.1
    assert dev._timeout == 1.1  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._io_timeout_ms == 1100  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 1.1 + 0.0  # 1 + io_timeout + lock_timeout

    dev.lock_timeout = -2.1
    assert dev._lock_timeout == vxi11.ONE_DAY  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._lock_timeout_ms == blocking_timeout_ms  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 1.1 + vxi11.ONE_DAY  # 1 + io_timeout + lock_timeout

    dev.lock_timeout = None
    assert dev._lock_timeout == vxi11.ONE_DAY  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._lock_timeout_ms == blocking_timeout_ms  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 1.1 + vxi11.ONE_DAY  # 1 + io_timeout + lock_timeout

    dev.lock_timeout = 0
    assert dev._lock_timeout == 0.0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._lock_timeout_ms == 0  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 1.1 + 0.0  # 1 + io_timeout + lock_timeout

    dev.lock_timeout = 1.2
    assert dev._lock_timeout == 1.2  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev._lock_timeout_ms == 1200  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert dev.socket.gettimeout() == 1.0 + 1.1 + 1.2  # 1 + io_timeout + lock_timeout

    dev.timeout = 0.5
    dev.lock_timeout = 0.5

    with pytest.raises(MSLTimeoutError):
        _ = dev.write("CONTINUE")

    dev.disconnect()

    rpc_program.stop()


def test_query_idn(tcp_server: type[TCPServer]) -> None:
    idn = b"Manufacturer of the Device,Model,Serial,dd.mm.yyyy  \n"

    # Don't start a PORT Mapping server, specify `port` value in Connection.properties
    rpc_program = tcp_server(term=None)
    rpc_program.start()

    timeout = 1
    connection = Connection(f"TCPIP::{rpc_program.host}", timeout=timeout, port=rpc_program.port)

    xid = 1  # first transaction sent to rpc_program to request a link ID
    vxi_error_code = 0
    link_id = 1
    abort_port = 619
    max_recv_size = 1024

    # create_link() response
    msg = (
        b"\x80\x00\x00("  # fragment size is 40 bytes, ( is ASCII 40
        + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">4L", vxi_error_code, link_id, abort_port, max_recv_size)  # 16 bytes
    )
    rpc_program.add_response(msg)

    # returns the number of bytes received from the "*IDN?" request
    msg = (
        b"\x80\x00\x00 "  # fragment size is 32 bytes, SPACE is ASCII 32
        + struct.pack(">3I", xid + 1, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">2L", vxi_error_code, len("*IDN?"))  # 8 bytes
    )
    rpc_program.add_response(msg)

    # returns the *IDN? response
    msg = (
        b"\x80\x00\x00\\"  # fragment size is 92 bytes, \ is ASCII 92
        + struct.pack(">3I", xid + 2, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">3L", vxi_error_code, vxi11.RX_END, len(idn))  # 12 bytes
        + idn  # 53 bytes
        + b"\x00\x00\x00"  # 3 bytes (opaque padding)
    )
    rpc_program.add_response(msg)

    # destroy_link() response
    msg = (
        b"\x80\x00\x00\x1c"  # last fragment, fragment size is 28 bytes \x1c
        + struct.pack(">3I", xid + 3, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">L", vxi_error_code)  # 4 bytes
    )
    rpc_program.add_response(msg)

    dev = connection.connect()
    assert dev.timeout == timeout
    assert dev.lock_timeout == 0
    assert dev.read_termination is None
    assert dev.write_termination is None
    assert dev.write("*IDN?") == 5
    assert dev.read(decode=False) == idn
    dev.disconnect()

    rpc_program.stop()


def test_vxi_error(tcp_server: type[TCPServer]) -> None:
    idn = b"Manufacturer of the Device,Model,Serial,dd.mm.yyyy  \n"

    # Don't start a PORT Mapping server, specify `port` value in Connection.properties
    rpc_program = tcp_server(term=None)
    rpc_program.start()

    timeout = 1
    connection = Connection(f"TCPIP::{rpc_program.host}", timeout=timeout, port=rpc_program.port)

    xid = 1  # first transaction sent to rpc_program to request a link ID
    vxi_error_code = 0
    link_id = 1
    abort_port = 619
    max_recv_size = 1024  #  struct.pack(">L", 1024) ends with \x00 which is the termination character

    # create_link() response
    msg = (
        b"\x80\x00\x00("  # fragment size is 40 bytes, ( is ASCII 40
        + struct.pack(">3I", xid, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">4L", vxi_error_code, link_id, abort_port, max_recv_size)  # 16 bytes
    )
    rpc_program.add_response(msg)

    # returns the number of bytes received from the "*IDN?" request
    msg = (
        b"\x80\x00\x00 "  # fragment size is 32 bytes, SPACE is ASCII 32
        + struct.pack(">3I", xid + 1, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">2L", vxi_error_code, len("*IDN?"))  # 8 bytes
    )
    rpc_program.add_response(msg)

    # returns the *IDN? response
    vxi_error_code = 3
    msg = (
        b"\x80\x00\x00\\"  # fragment size is 92 bytes, \ is ASCII 92
        + struct.pack(">3I", xid + 2, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">3L", vxi_error_code, vxi11.RX_END, len(idn))  # 12 bytes
        + idn  # 53 bytes
        + b"\x00\x00\x00"  # 3 bytes (opaque padding)
    )
    rpc_program.add_response(msg)

    # destroy_link() response
    vxi_error_code = 0
    msg = (
        b"\x80\x00\x00\x1c"  # last fragment, fragment size is 28 bytes \x1c
        + struct.pack(">3I", xid + 3, MessageType.REPLY, ReplyStatus.MSG_ACCEPTED)  # 12 bytes
        + struct.pack(">QI", 0, AcceptStatus.SUCCESS)  # 12 bytes
        + struct.pack(">L", vxi_error_code)  # 4 bytes
    )
    rpc_program.add_response(msg)

    dev = connection.connect()
    assert dev.timeout == timeout
    assert dev.lock_timeout == 0
    assert dev.read_termination is None
    assert dev.write_termination is None
    assert dev.write("*IDN?") == 5
    with pytest.raises(MSLConnectionError, match=vxi11.VXI_ERROR_CODES[3]):
        _ = dev.read(decode=False)
    dev.disconnect()

    rpc_program.stop()


def test_invalid_address() -> None:
    with pytest.raises(ValueError, match=r"Invalid VXI-11 address 'COM3'"):
        _ = VXI11(Equipment(connection=Connection("COM3")))


def test_cannot_connect() -> None:
    connection = Connection("TCPIP::127.0.0.1", timeout=0.2)
    with pytest.raises((MSLConnectionError, MSLTimeoutError)):
        _ = connection.connect()


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = VXI11(Equipment())
