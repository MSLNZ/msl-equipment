from __future__ import annotations

import struct
import sys
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from msl.equipment import Connection, Equipment, Modbus, MSLConnectionError, Serial, Socket
from msl.equipment.interfaces.modbus import (
    ASCIIFramer,
    FramerType,
    ModbusResponse,
    ParsedModbusAddress,
    RTUFramer,
    SocketFramer,
    find_modbus,
    parse_modbus_address,
)

if TYPE_CHECKING:
    from conftest import TCPServer, UDPServer
    from tests.protocol_mock import SerialServer


PREFIX = "COM" if sys.platform == "win32" else "ASRL"


def cast_server(dev: Modbus) -> SerialServer:
    assert isinstance(dev.interface, Serial)
    return cast("SerialServer", cast("object", dev.interface.serial))


@pytest.mark.parametrize(
    "address",
    [
        "",
        "COM2",
        "ASRL/dev/ttyUSB1",
        "TCP::192.168.1.100::502",
        "Prologix::COM6",
        "MODBUS::COM4::INVALID",
        "MODBUS::1.2.3.4::INVALID",
        "MODBUS::1.2.3.4::502::INVALID",
    ],
)
def test_parse_address_invalid(address: str) -> None:
    assert parse_modbus_address(address) is None


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("MODBUS::COM8", ParsedModbusAddress(address="COM8", framer=FramerType.RTU)),
        ("Modbus::COM12::RTU", ParsedModbusAddress(address="COM12", framer=FramerType.RTU)),
        ("modbus::COM1::ascii", ParsedModbusAddress(address="COM1", framer=FramerType.ASCII)),
        ("MODBUS::COM12::udp", ParsedModbusAddress(address="COM12", framer=FramerType.RTU)),  # udp ignored
        ("MODBUS::/dev/ttyS0", ParsedModbusAddress(address="ASRL/dev/ttyS0", framer=FramerType.RTU)),
        ("MODBUS::/dev/1.2::rtu", ParsedModbusAddress(address="ASRL/dev/1.2", framer=FramerType.RTU)),
        ("MODBUS::/dev/1.2::ASCII", ParsedModbusAddress(address="ASRL/dev/1.2", framer=FramerType.ASCII)),
        ("MODBUS::/dev/1.2::UDP", ParsedModbusAddress(address="ASRL/dev/1.2", framer=FramerType.RTU)),  # UDP ignored
        ("MODBUS::1.2.3.4", ParsedModbusAddress(address="TCP::1.2.3.4::502", framer=FramerType.SOCKET)),
        ("MODBUS::1.2.3.4::1", ParsedModbusAddress(address="TCP::1.2.3.4::1", framer=FramerType.SOCKET)),
        ("MODBUS::abc::621::AscII", ParsedModbusAddress(address="TCP::abc::621", framer=FramerType.ASCII)),
        ("MODBUS::a::621::rtu", ParsedModbusAddress(address="TCP::a::621", framer=FramerType.RTU)),
        ("MODBUS::ASCII", ParsedModbusAddress(address="TCP::ASCII::502", framer=FramerType.SOCKET)),
        ("MODBUS::rtu::rtu", ParsedModbusAddress(address="TCP::rtu::502", framer=FramerType.RTU)),
        (
            "MODBUS::company-com::1234::SOCKET",
            ParsedModbusAddress(address="TCP::company-com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::company-com::1234::SOCKET::UDP",
            ParsedModbusAddress(address="UDP::company-com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::company-com::1234::UDP",
            ParsedModbusAddress(address="UDP::company-com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::192.168.1.100::UDP",
            ParsedModbusAddress(address="UDP::192.168.1.100::502", framer=FramerType.SOCKET),
        ),
        ("MODBUS::/mock://", ParsedModbusAddress(address="ASRL/mock://", framer=FramerType.RTU)),
        ("MoDbUs::/mock://::ascII", ParsedModbusAddress(address="ASRL/mock://", framer=FramerType.ASCII)),
        ("Modbus::?::VID=12&PID=34", ParsedModbusAddress(address=f"{PREFIX}?::VID=12&PID=34", framer=FramerType.RTU)),
        (
            "ModBUS::?::a1 [,.&*^] bc::ASCII",
            ParsedModbusAddress(address=f"{PREFIX}?::a1 [,.&*^] bc", framer=FramerType.ASCII),
        ),
        (
            "MODBUS::?::(Company|Name)::RTU",
            ParsedModbusAddress(address=f"{PREFIX}?::(Company|Name)", framer=FramerType.RTU),
        ),
    ],
)
def test_parse_address_valid(address: str, expected: ParsedModbusAddress) -> None:
    assert parse_modbus_address(address) == expected


@pytest.mark.parametrize(
    ("payload", "crc"),
    [
        (b"\x02\x01\x00\x20\x00\x0c", b"\x3d\xf6"),
        (b"\x02\x01\x02\x80\x02", b"\x1d\xfd"),
        (b"\x01\x02\x01\xf4\x00\x20", b"\x39\xdc"),
        (b"\x01\x02\x02\x05\x00", b"\xba\xe8"),
        (b"\x01\x03\x02\x58\x00\x02", b"\x44\x60"),
        (b"\x01\x03\x04\x03\xe8\x13\x88", b"\x77\x15"),
        (b"\x1c\x10\x00\x64\x00\x02\x04\x03\xe8\x07\xd8", b"\x19\x02"),
        (b"\x1c\x10\x00\x64\x00\x02", b"\x03\x9a"),
        (b"\x01\x04\x00\xc8\x00\x02", b"\xf0\x35"),
        (b"\x01\x04\x04\x27\x10\xc3\x50", b"\xa0\x39"),
    ],
)
def test_crc(payload: bytes, crc: bytes) -> None:
    assert RTUFramer.calculate_crc(payload) == crc


@pytest.mark.parametrize(
    ("payload", "lrc"),
    [
        (b"\x04\x01\x00\x0a\x00\x0d", 0xE4),
        (b"\x04\x01\x02\x0a\x11", 0xDE),
        (b"\x04\x02\x00\x0a\x00\x0d", 0xE3),
        (b"\x04\x02\x02\x0a\x11", 0xDD),
        (b"\x01\x03\x00\x00\x00\x02", 0xFA),
        (b"\x01\x03\x04\x00\x06\x00\x05", 0xED),
        (b"\x01\x04\x00\x00\x00\x02", 0xF9),
        (b"\x01\x04\x04\x00\x06\x00\x05", 0xEC),
        (b"\x11\x05\x00\xac\x00\xff", 0x3F),
        (b"\x11\x06\x00\x01\x00\x03", 0xE5),
        (b"\x11\x0f\x00\x13\x00\x0a\x02\xcd\x01", 0xF3),
        (b"\x11\x0f\x00\x13\x00\x0a", 0xC3),
        (b"\x11\x10\x00\x01\x00\x02\x04\x0a\x01\x02", 0xCB),
        (b"\x11\x10\x00\x01\x00\x02", 0xDC),
    ],
)
def test_lrc(payload: bytes, lrc: int) -> None:
    assert ASCIIFramer.calculate_lrc(payload) == lrc


def test_modbus_response_str() -> None:
    mr = ModbusResponse(1, 2, b"")
    assert mr.data == b""
    assert mr.device_id == 1
    assert mr.function_code == 2
    assert str(mr) == "ModbusResponse(device_id=1, function_code=0x02, data=b'')"

    mr = ModbusResponse(200, 10, b"Hello")
    assert mr.data == b"Hello"
    assert mr.device_id == 200
    assert mr.function_code == 10
    assert str(mr) == "ModbusResponse(device_id=200, function_code=0x0A, data=b'Hello')"


def test_modbus_response_int16() -> None:
    mr = ModbusResponse(1, 1, b"\xfc\x18")
    assert mr.int16() == -1000
    assert mr.int16("big") == -1000
    assert mr.int16("little") == 6396


def test_modbus_response_uint16() -> None:
    mr = ModbusResponse(1, 1, bytes([48, 57]))
    assert mr.uint16() == 12345
    assert mr.uint16("big") == 12345
    assert mr.uint16("little") == 14640


def test_modbus_response_int32() -> None:
    mr = ModbusResponse(1, 1, b"\xff\xf0\xbd\xc0")
    assert mr.int32() == -1_000_000
    assert mr.int32("big") == -1_000_000
    assert mr.int32("little") == -1061293825


def test_modbus_response_uint32() -> None:
    mr = ModbusResponse(1, 1, b"\x07[\xcd\x15")
    assert mr.uint32() == 123456789
    assert mr.uint32("big") == 123456789
    assert mr.uint32("little") == 365779719


def test_modbus_response_int64() -> None:
    mr = ModbusResponse(1, 1, b"\xff\xff\xfc\x00\x00\x00\x00\x00")
    assert mr.int64() == -4398046511104
    assert mr.int64("big") == -4398046511104
    assert mr.int64("little") == 16580607


def test_modbus_response_uint64() -> None:
    mr = ModbusResponse(1, 1, b"\x00\x00\x04\x00\x00\x00\x00\x00")
    assert mr.uint64() == 4398046511104
    assert mr.uint64("big") == 4398046511104
    assert mr.uint64("little") == 262144


def test_modbus_response_float32() -> None:
    mr = ModbusResponse(1, 1, b"Dz\x00\x00")
    assert mr.float32() == 1000.0
    assert mr.float32("big") == 1000.0
    assert mr.float32("little") == 4.3860641933366774e-41


def test_modbus_response_float64() -> None:
    mr = ModbusResponse(1, 1, b"\xc12\xc4\xb0\x00\x00\x00\x00")
    assert mr.float64() == -1.23e6
    assert mr.float64("big") == -1.23e6
    assert mr.float64("little") == 1.4652248266e-314


def test_modbus_response_nan_inf() -> None:
    mr = ModbusResponse(1, 1, data=b"\xff\xc0\x00\x00")
    assert np.isnan(mr.float32())

    mr = ModbusResponse(1, 1, data=b"\x7f\x80\x00\x00")
    assert np.isinf(mr.float32())

    mr = ModbusResponse(1, 1, data=b"\x7f\xf8\x00\x00\x00\x00\x00\x00")
    assert np.isnan(mr.float64())

    mr = ModbusResponse(1, 1, data=b"\x7f\xf0\x00\x00\x00\x00\x00\x00")
    assert np.isinf(mr.float64())


def test_modbus_response_decode() -> None:
    mr = ModbusResponse(1, 1, b"hello")
    assert mr.decode() == "hello"
    assert mr.decode("ascii") == "hello"

    with pytest.raises(LookupError):
        _ = mr.decode("invalid")


def test_modbus_response_array_i4() -> None:
    data = np.array([45, -825, 62982, 34104852], dtype=np.int32)
    mr = ModbusResponse(1, 1, data.tobytes())

    big = np.frombuffer(data.tobytes(), dtype=">i4")
    little = np.frombuffer(data.tobytes(), dtype="<i4")
    assert np.array_equal(mr.array("i4"), big)
    assert np.array_equal(mr.array("int32"), big)
    assert np.array_equal(mr.array(">i4"), big)
    assert np.array_equal(mr.array("<i4"), little)
    assert np.array_equal(mr.array(np.int32), big)
    assert np.array_equal(mr.array(np.dtype(">i4")), big)
    assert np.array_equal(mr.array(np.dtype("<i4")), little)


def test_modbus_response_array_f4() -> None:
    data = b"\x40\xf8\x11\x5f\x40\xd4\x8c\x8a\x40\xb5\xbb\x8a\x40\x90\x78\x9c"
    mr = ModbusResponse(1, 1, data)

    big = np.frombuffer(data, dtype=">f4")
    little = np.frombuffer(data, dtype="<f4")
    assert np.array_equal(mr.array("f4"), big)
    assert np.array_equal(mr.array("float32"), big)
    assert np.array_equal(mr.array(">f4"), big)
    assert np.array_equal(mr.array("<f4"), little)
    assert np.array_equal(mr.array(np.float32), big)
    assert np.array_equal(mr.array(np.dtype(">f4")), big)
    assert np.array_equal(mr.array(np.dtype("<f4")), little)


def test_modbus_response_array_f8() -> None:
    data = b"\x40\xf8\x11\x5f\x40\xd4\x8c\x8a\x40\xb5\xbb\x8a\x40\x90\x78\x9c"
    mr = ModbusResponse(1, 1, data)

    big = np.frombuffer(data, dtype=">f8")
    little = np.frombuffer(data, dtype="<f8")
    assert np.array_equal(mr.array("f8"), big)
    assert np.array_equal(mr.array("float64"), big)
    assert np.array_equal(mr.array(">f8"), big)
    assert np.array_equal(mr.array("<f8"), little)
    assert np.array_equal(mr.array(np.float64), big)
    assert np.array_equal(mr.array(float), big)
    assert np.array_equal(mr.array(np.dtype(">f8")), big)
    assert np.array_equal(mr.array(np.dtype("<f8")), little)


def test_modbus_response_bits() -> None:
    mr = ModbusResponse(1, 1, b"\x01")
    assert np.array_equal(mr.bits(), [True, False, False, False, False, False, False, False])
    assert np.array_equal(mr.bits("big"), [False, False, False, False, False, False, False, True])

    mr = ModbusResponse(1, 1, b"\x01", count=1)
    assert np.array_equal(mr.bits(), [True])
    assert np.array_equal(mr.bits("big"), [False])

    mr = ModbusResponse(1, 1, 0b0110_0001.to_bytes(1, "big"), count=7)
    assert np.array_equal(mr.bits(), [True, False, False, False, False, True, True])
    assert np.array_equal(mr.bits("big"), [False, True, True, False, False, False, False])

    mr = ModbusResponse(1, 1, 0b0110_0001.to_bytes(1, "big"), count=8)
    assert np.array_equal(mr.bits(), [True, False, False, False, False, True, True, False])
    assert np.array_equal(mr.bits("big"), [False, True, True, False, False, False, False, True])


def test_to_register_values() -> None:
    expected = np.array([2], dtype=np.uint16)
    array = Modbus.to_register_values(2)
    assert np.array_equal(array, expected)
    array = Modbus.to_register_values(np.array([2], np.uint16))
    assert np.array_equal(array, expected)

    expected = np.array([18, 54919], dtype=np.uint16)
    array = Modbus.to_register_values(1234567, "u4")
    assert np.array_equal(array, expected)
    array = Modbus.to_register_values(np.array([1234567], np.uint32))
    assert np.array_equal(array, expected)

    expected = np.array([65535, 64302], dtype=np.uint16)
    array = Modbus.to_register_values(-1234, "i4")
    assert np.array_equal(array, expected)
    array = Modbus.to_register_values(np.array([-1234], np.int32))
    assert np.array_equal(array, expected)

    expected = np.array([16285, 62390], dtype=np.uint16)
    array = Modbus.to_register_values(1.234, "f4")
    assert np.array_equal(array, expected)
    array = Modbus.to_register_values(np.array([1.234], np.float32))
    assert np.array_equal(array, expected)


def test_connect_timeout() -> None:
    match = r"^Modbus<|| at TCP::127.0.0.1::41983>\nTimeout occurred after 0.01 second\(s\)"
    with pytest.raises(MSLConnectionError, match=match):
        _ = Connection("Modbus::127.0.0.1::41983", timeout=0.01).connect()

    with pytest.raises(MSLConnectionError, match=r"^Modbus<|| at COM254>"):
        _ = Connection("Modbus::COM254", timeout=0.01).connect()


def test_invalid_modbus_address() -> None:
    # Does not start with "Modbus::"
    with pytest.raises(ValueError, match=r"Invalid Modbus address 'COM6'"):
        _ = Modbus(Equipment(connection=Connection("COM6")))


def test_tcp_repr_str(tcp_server: type[TCPServer]) -> None:
    with tcp_server() as server:
        connection = Connection(
            f"Modbus::{server.host}::{server.port}", manufacturer="A", model="B", serial="C", timeout=1
        )

        dev: Modbus = connection.connect()
        assert dev.timeout == 1.0
        dev.timeout = None
        assert dev.timeout is None
        assert str(dev) == "Modbus<A|B|C>"
        assert repr(dev) == f"Modbus<A|B|C at TCP::{server.host}::{server.port}>"
        assert isinstance(dev.interface, Socket)
        dev.disconnect()


def test_udp_repr_str(udp_server: type[UDPServer]) -> None:
    with udp_server() as server:
        connection = Connection(
            f"Modbus::{server.host}::{server.port}::UDP", manufacturer="A", model="B", serial="C", timeout=0.9
        )

        dev: Modbus = connection.connect()
        assert str(dev) == "Modbus<A|B|C>"
        assert repr(dev) == f"Modbus<A|B|C at UDP::{server.host}::{server.port}>"
        assert dev.timeout == 0.9
        assert isinstance(dev.interface, Socket)
        dev.disconnect()


def test_rtu_repr_str() -> None:
    connection = Connection(
        "Modbus::/mock://",
        manufacturer="A",
        model="B",
        serial="C",
        baudrate=19200,
        bytesize=7,
        parity="E",
        stopbits=2,
        timeout=0.9,
    )

    dev: Modbus = connection.connect()
    assert str(dev) == "Modbus<A|B|C>"
    assert repr(dev) == "Modbus<A|B|C at ASRL/mock://>"
    assert dev.timeout == 0.9
    iface = cast("Serial", dev.interface)
    assert iface.serial.baudrate == 19200
    assert iface.serial.bytesize == 7
    assert iface.serial.parity == "E"
    assert iface.serial.stopbits == 2
    assert isinstance(dev.interface, Serial)
    dev.disconnect()


def test_tcp_transaction_id(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            framer = dev._framer  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            assert isinstance(framer, SocketFramer)
            assert framer.transaction_id == 0

            assert framer.write(device_id=1, pdu=b"") == 7
            assert framer.read() == (1, b"")
            assert framer.transaction_id == 1

            assert framer.write(device_id=10, pdu=b"a") == 8
            assert framer.read() == (10, b"a")
            assert framer.transaction_id == 2

            framer.transaction_id = 65534

            assert framer.write(device_id=22, pdu=b"ab") == 9
            assert framer.read() == (22, b"ab")
            assert framer.transaction_id == 65535

            assert framer.write(device_id=33, pdu=b"abc") == 10
            assert framer.read() == (33, b"abc")
            assert framer.transaction_id == 1

            assert framer.write(device_id=215, pdu=b"abcd") == 11
            assert framer.read() == (215, b"abcd")
            assert framer.transaction_id == 2


def test_tcp_modbus_exception_code(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            assert dev.write(130, data=b"\x01") == 9
            with pytest.raises(MSLConnectionError, match=r"function code is not supported"):
                _ = dev.read()

            assert dev.write(130, data=b"\x04") == 9
            with pytest.raises(MSLConnectionError, match=r"unrecoverable error occurred"):
                _ = dev.read()

            assert dev.write(130, data=b"\x0d") == 9
            with pytest.raises(MSLConnectionError, match=r"Unknown Modbus exception code 0x0D"):
                _ = dev.read()


def test_rtu_modbus_exception_code() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()

    assert dev.write(130, data=b"\x03") == 5
    with pytest.raises(MSLConnectionError, match=r"Modbus request message is invalid"):
        _ = dev.read()

    assert dev.write(130, data=b"\x02") == 5
    with pytest.raises(MSLConnectionError, match=r"Invalid Modbus register address"):
        _ = dev.read()

    assert dev.write(130, data=b"\x0d") == 5
    with pytest.raises(MSLConnectionError, match=r"Unknown Modbus exception code 0x0D"):
        _ = dev.read()

    dev.disconnect()


def test_ascii_modbus_exception_code() -> None:
    dev: Modbus = Connection("Modbus::/mock://::ASCII").connect()

    assert dev.write(130, data=b"\x01") == 11
    with pytest.raises(MSLConnectionError, match=r"function code is not supported"):
        _ = dev.read()

    assert dev.write(130, data=b"\x04") == 11
    with pytest.raises(MSLConnectionError, match=r"unrecoverable error occurred"):
        _ = dev.read()

    assert dev.write(130, data=b"\x0d") == 11
    with pytest.raises(MSLConnectionError, match=r"Unknown Modbus exception code 0x0D"):
        _ = dev.read()

    dev.disconnect()


def test_tcp_read_coils(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"2001 coils, maximum allowed is 2000"):
                _ = dev.read_coils(1, count=2001)

            mr = dev.read_coils(5130, count=17, device_id=240)
            assert mr.data == b"\n\x00\x11"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x14\n\x00\x11'
            assert mr.count == 17
            assert mr.device_id == 240
            assert mr.function_code == 1

            # Response from MODBUS Application Protocol Specification V1.1b3
            server.add_response(b"\x00\x02\x00\x00\x00\x06\xf0\x01\x03\xcd\x6b\x05")
            mr = dev.read_coils(0, count=8 + 8 + 3)  # address ignored
            assert mr.data == b"\xcd\x6b\x05"
            assert mr.count == 19
            assert mr.device_id == 240  # \xF0
            assert mr.function_code == 1
            # fmt: off
            # 1  1  0  0  1  1  0  1   0  1  1  0  1  0  1  1   0 0 0 0 0 1  0  1
            # 27 26 25 24 23 22 21 20  35 34 33 32 31 30 29 28  X X X X X 38 37 36
            assert np.array_equal(mr.bits(), [
                # 20     21    22    23     24     25    26    27    28    29     30    31     32    33    34     35    36     37    38  # noqa: E501
                True, False, True, True, False, False, True, True, True, True, False, True, False, True, True, False, True, False, True  # noqa: E501
            ])
            # fmt: on

            server.add_response(b"\x00\x03\x00\x00\x00\x04\xf0\x01\x01\x01")
            mr = dev.read_coils(0)  # address ignored
            assert mr.data == b"\x01"
            assert mr.count == 1
            assert mr.device_id == 240  # \xF0
            assert mr.function_code == 1
            assert np.array_equal(mr.bits(), [True])
            assert np.array_equal(mr.bits("big"), [False])
            mr.count = None
            assert np.array_equal(mr.bits(), [True, False, False, False, False, False, False, False])
            assert np.array_equal(mr.bits("big"), [False, False, False, False, False, False, False, True])

            server.add_response(b"\x00\x03\x00\x00\x00\x03\x01\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 3, expected 4$"):
                _ = dev.read_coils(0)

            server.add_response(b"\x00\x05\x00\x00\x00\x04\x01\x02\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x01$"):
                _ = dev.read_coils(0)

            # https://github.com/pymodbus-dev/pymodbus/issues/2630
            server.add_response(b"\x00\x06\x00\x00\x00\x05\xf1\x01\x02\xf5\xff")
            mr = dev.read_coils(0, count=16)  # address ignored
            assert mr.data == b"\xf5\xff"
            assert mr.count == 16
            assert mr.device_id == 241  # \xF1
            assert mr.function_code == 1
            assert np.array_equal(
                mr.bits(),
                [True, False, True, False, True, True, True, True, True, True, True, True, True, True, True, True],
            )

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readCoils
            server.add_response(b"\x00\x07\x00\x00\x00\x05\x02\x01\x02\x80\x02")
            mr = dev.read_coils(0, count=12)  # address ignored
            assert mr.data == b"\x80\x02"
            assert mr.count == 12
            assert mr.device_id == 2
            assert mr.function_code == 1
            assert np.array_equal(
                #      33     34     35     36     37     38     39    40     41    42     43     44
                [False, False, False, False, False, False, False, True, False, True, False, False],
                mr.bits(),
            )


def test_rtu_read_coils() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    with pytest.raises(ValueError, match=r"2001 coils, maximum allowed is 2000"):
        _ = dev.read_coils(1, count=2001)

    # Response from MODBUS Application Protocol Specification V1.1b3
    server.add_response(b"\xf0\x01\x03\xcd\x6b\x05\x57\xa3")
    mr = dev.read_coils(0, count=8 + 8 + 3)  # address ignored
    assert mr.data == b"\xcd\x6b\x05"
    assert mr.count == 19
    assert mr.device_id == 240  # \xf0
    assert mr.function_code == 1
    # fmt: off
    # 1  1  0  0  1  1  0  1   0  1  1  0  1  0  1  1   0 0 0 0 0 1  0  1
    # 27 26 25 24 23 22 21 20  35 34 33 32 31 30 29 28  X X X X X 38 37 36
    assert np.array_equal(mr.bits(), [
        # 20     21    22    23     24     25    26    27    28    29     30    31     32    33    34     35    36     37    38  # noqa: E501
        True, False, True, True, False, False, True, True, True, True, False, True, False, True, True, False, True, False, True  # noqa: E501
    ])
    # fmt: on

    server.add_response(b"\xf0\x01\x03\xcd\x6b\x05\x00\x11")
    with pytest.raises(MSLConnectionError, match=r"0x0011, expected 0x57a3"):
        _ = dev.read_coils(0, count=19)  # address ignored

    server.add_response(b"\xf0\x01\x01\x01\xa2\xb4")
    mr = dev.read_coils(0)  # address ignored
    assert mr.data == b"\x01"
    assert mr.count == 1
    assert mr.device_id == 240  # \xf0
    assert mr.function_code == 1
    assert np.array_equal(mr.bits(), [True])
    assert np.array_equal(mr.bits("big"), [False])
    mr.count = None
    assert np.array_equal(mr.bits(), [True, False, False, False, False, False, False, False])
    assert np.array_equal(mr.bits("big"), [False, False, False, False, False, False, False, True])

    server.add_response(b"\x01\x02\x01\x01\x60\x48")
    with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x01$"):
        _ = dev.read_coils(0)

    # https://github.com/pymodbus-dev/pymodbus/issues/2630
    server.add_response(b"\xf1\x01\x02\xf5\xff\xfe\xf9")
    mr = dev.read_coils(0, count=16)  # address ignored
    assert mr.data == b"\xf5\xff"
    assert mr.count == 16
    assert mr.device_id == 241  # \xf1
    assert mr.function_code == 1
    assert np.array_equal(
        mr.bits(),
        [True, False, True, False, True, True, True, True, True, True, True, True, True, True, True, True],
    )

    # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readCoils
    server.add_response(b"\x02\x01\x02\x80\x02\x1d\xfd")
    mr = dev.read_coils(0, count=12, device_id=2)  # address ignored
    assert mr.data == b"\x80\x02"
    assert mr.count == 12
    assert mr.device_id == 2
    assert mr.function_code == 1
    assert np.array_equal(
        #      33     34     35     36     37     38     39    40     41    42     43     44
        [False, False, False, False, False, False, False, True, False, True, False, False],
        mr.bits(),
    )

    dev.disconnect()


def test_tcp_read_discrete_inputs(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"2001 discrete inputs, maximum allowed is 2000"):
                _ = dev.read_discrete_inputs(1, count=2001)

            mr = dev.read_discrete_inputs(1020, count=10, device_id=31)
            assert mr.data == b"\xfc\x00\n"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x03\xfc\x00\n'
            assert mr.count == 10
            assert mr.device_id == 31
            assert mr.function_code == 2

            # Response from MODBUS Application Protocol Specification V1.1b3
            server.add_response(b"\x00\x02\x00\x00\x00\x06\x04\x02\x03\xac\xdb\x35")
            mr = dev.read_discrete_inputs(0, count=8 + 8 + 6)  # address ignored
            assert mr.data == b"\xac\xdb\x35"
            assert mr.count == 22
            assert mr.device_id == 4
            assert mr.function_code == 2
            # fmt: off
            #   1   0   1   0   1   1   0   0    1   1   0   1   1   0   1   1  0 0   1   1   0   1   0   1
            # 204 203 202 201 200 199 198 197  212 211 210 209 208 207 206 205  X X 218 217 216 215 214 213
            assert np.array_equal(mr.bits(), [
                # 197    198   199   200    201   202    203   204   205   206    207   208   209    210   211   212   213    214   215    216   217   218  # noqa: E501
                False, False, True, True, False, True, False, True, True, True, False, True, True, False, True, True, True, False, True, False, True, True  # noqa: E501
            ])
            # fmt: on

            server.add_response(b"\x00\x03\x00\x00\x00\x04\xf0\x02\x01\x01")
            mr = dev.read_discrete_inputs(0)  # address ignored
            assert mr.data == b"\x01"
            assert mr.count == 1
            assert mr.device_id == 240  # \xf0
            assert mr.function_code == 2
            assert np.array_equal(mr.bits(), [True])
            assert np.array_equal(mr.bits("big"), [False])
            mr.count = None
            assert np.array_equal(mr.bits(), [True, False, False, False, False, False, False, False])
            assert np.array_equal(mr.bits("big"), [False, False, False, False, False, False, False, True])

            server.add_response(b"\x00\x01\x00\x00\x00\x03\x02\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 4$"):
                _ = dev.read_discrete_inputs(0)

            server.add_response(b"\x00\x05\x00\x00\x00\x04\x01\x05\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"function code 0x05, expected 0x02$"):
                _ = dev.read_discrete_inputs(0)

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readInputs
            server.add_response(b"\x00\x06\x00\x00\x00\x05\x08\x02\x02\x05\x00")
            mr = dev.read_discrete_inputs(0, count=16)  # address ignored
            assert mr.data == b"\x05\x00"
            assert mr.count == 16
            assert mr.device_id == 8
            assert mr.function_code == 2
            assert np.array_equal(mr.bits(), [True, False, True] + [False] * 13)


def test_rtu_read_discrete_inputs() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    with pytest.raises(ValueError, match=r"2001 discrete inputs, maximum allowed is 2000"):
        _ = dev.read_discrete_inputs(1, count=2001)

    # Response from MODBUS Application Protocol Specification V1.1b3
    server.add_response(b"\x04\x02\x03\xac\xdb\x35\x22\xdd")
    mr = dev.read_discrete_inputs(0, count=8 + 8 + 6)  # address ignored
    assert mr.data == b"\xac\xdb\x35"
    assert mr.count == 22
    assert mr.device_id == 4
    assert mr.function_code == 2
    # fmt: off
    #   1   0   1   0   1   1   0   0    1   1   0   1   1   0   1   1  0 0   1   1   0   1   0   1
    # 204 203 202 201 200 199 198 197  212 211 210 209 208 207 206 205  X X 218 217 216 215 214 213
    assert np.array_equal(mr.bits(), [
        # 197    198   199   200    201   202    203   204   205   206    207   208   209    210   211   212   213    214   215    216   217   218  # noqa: E501
        False, False, True, True, False, True, False, True, True, True, False, True, True, False, True, True, True, False, True, False, True, True  # noqa: E501
    ])
    # fmt: on

    server.add_response(b"\xf0\x02\x01\x01\x52\xb4")
    mr = dev.read_discrete_inputs(0)  # address ignored
    assert mr.data == b"\x01"
    assert mr.count == 1
    assert mr.device_id == 240  # \xf0
    assert mr.function_code == 2
    assert np.array_equal(mr.bits(), [True])
    assert np.array_equal(mr.bits("big"), [False])
    mr.count = None
    assert np.array_equal(mr.bits(), [True, False, False, False, False, False, False, False])
    assert np.array_equal(mr.bits("big"), [False, False, False, False, False, False, False, True])

    server.add_response(b"\x01\x01\x01\x01\x90\x48")
    with pytest.raises(MSLConnectionError, match=r"function code 0x01, expected 0x02$"):
        _ = dev.read_discrete_inputs(0)

    # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readInputs
    server.add_response(b"\x08\x02\x02\x05\x00\x66\xe9")
    mr = dev.read_discrete_inputs(0, count=16)  # address ignored
    assert mr.data == b"\x05\x00"
    assert mr.count == 16
    assert mr.device_id == 8
    assert mr.function_code == 2
    assert np.array_equal(mr.bits(), [True, False, True] + [False] * 13)

    dev.disconnect()


def test_tcp_read_holding_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
                _ = dev.read_holding_registers(1, count=126)

            server.add_response(b"\x00\x01\x00\x00\x00\x09\x02\x03\x06\x02\x2b\x00\x00\x00\x64")
            mr = dev.read_holding_registers(0, count=3)
            assert mr.count == 3
            assert mr.data == b"\x02\x2b\x00\x00\x00\x64"
            assert mr.device_id == 2
            assert mr.function_code == 3
            assert np.array_equal(mr.array("u2"), [555, 0, 100])

            server.add_response(b"\x00\x01\x00\x00\x00\x07\x01\x03\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 2$"):
                _ = dev.read_holding_registers(0)

            server.add_response(b"\x00\x03\x00\x00\x00\x07\x01\x02\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x03$"):
                _ = dev.read_holding_registers(0)

            server.add_response(b"\x00\x04\x00\x00\x00\x05\x01\x03\x02\xa0\x11")
            mr = dev.read_holding_registers(0, count=1)
            assert mr.count == 1
            assert mr.data == b"\xa0\x11"
            assert mr.device_id == 1
            assert mr.function_code == 3
            assert mr.uint16() == 40977

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readHoldingRegs
            server.add_response(b"\x00\x05\x00\x00\x00\x07\x01\x03\x04\x03\xe8\x13\x88")
            mr = dev.read_holding_registers(0, count=2)
            assert mr.count == 2
            assert mr.data == b"\x03\xe8\x13\x88"
            assert mr.device_id == 1
            assert mr.function_code == 3
            assert np.array_equal(mr.array("uint16"), [1000, 5000])


def test_rtu_read_holding_registers() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
        _ = dev.read_holding_registers(1, count=126)

    server.add_response(b"\x02\x03\x06\x02\x2b\x00\x00\x00\x64\x11\x8a")
    mr = dev.read_holding_registers(0, count=3)
    assert mr.count == 3
    assert mr.data == b"\x02\x2b\x00\x00\x00\x64"
    assert mr.device_id == 2
    assert mr.function_code == 3
    assert np.array_equal(mr.array("u2"), [555, 0, 100])

    server.add_response(b"\x01\x02\x04\x00\x11\x22\x33\xf3\x52")
    with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x03$"):
        _ = dev.read_holding_registers(0)

    server.add_response(b"\x01\x03\x02\xa0\x11\x00\x48")
    mr = dev.read_holding_registers(0, count=1)
    assert mr.count == 1
    assert mr.data == b"\xa0\x11"
    assert mr.device_id == 1
    assert mr.function_code == 3
    assert mr.uint16() == 40977

    # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readHoldingRegs
    server.add_response(b"\x01\x03\x04\x03\xe8\x13\x88\x77\x15")
    mr = dev.read_holding_registers(0, count=2)
    assert mr.count == 2
    assert mr.data == b"\x03\xe8\x13\x88"
    assert mr.device_id == 1
    assert mr.function_code == 3
    assert np.array_equal(mr.array("uint16"), [1000, 5000])

    dev.disconnect()


def test_tcp_read_input_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"input registers, maximum allowed is 125"):
                _ = dev.read_input_registers(1, count=126)

            server.add_response(b"\x00\x01\x00\x00\x00\x05\x01\x04\x02\x00\x11")
            mr = dev.read_input_registers(55100)
            assert mr.count == 1
            assert mr.data == b"\x00\x11"
            assert mr.device_id == 1
            assert mr.function_code == 4
            assert mr.uint16() == 17

            server.add_response(b"\x00\x01\x00\x00\x00\x07\x01\x04\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 2$"):
                _ = dev.read_input_registers(55100)

            server.add_response(b"\x00\x03\x00\x00\x00\x07\x01\x02\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x04$"):
                _ = dev.read_input_registers(55100)

            server.add_response(b"\x00\x04\x00\x00\x00\x07\x01\x04\x04\x00\x11\x22\x33")
            mr = dev.read_input_registers(55100, count=2)
            assert mr.count == 2
            assert mr.data == b"\x00\x11\x22\x33"
            assert mr.device_id == 1
            assert mr.function_code == 4
            assert mr.uint32() == 1122867


def test_rtu_read_input_registers() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    with pytest.raises(ValueError, match=r"input registers, maximum allowed is 125"):
        _ = dev.read_input_registers(1, count=126)

    server.add_response(b"\x01\x04\x02\x00\x11\x79\x3c")
    mr = dev.read_input_registers(55100)
    assert mr.count == 1
    assert mr.data == b"\x00\x11"
    assert mr.device_id == 1
    assert mr.function_code == 4
    assert mr.uint16() == 17

    server.add_response(b"\x01\x04\x04\x00\x11\x22\x33\x01\x23")
    with pytest.raises(MSLConnectionError, match=r"0x0123, expected 0xf334$"):
        _ = dev.read_input_registers(55100)

    server.add_response(b"\x01\x02\x04\x00\x11\x22\x33\xf3\x52")
    with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x04$"):
        _ = dev.read_input_registers(55100)

    server.add_response(b"\x01\x04\x04\x00\x11\x22\x33\xf3\x34")
    mr = dev.read_input_registers(55100, count=2)
    assert mr.count == 2
    assert mr.data == b"\x00\x11\x22\x33"
    assert mr.device_id == 1
    assert mr.function_code == 4
    assert mr.uint32() == 1122867

    dev.disconnect()


def test_tcp_read_exception_status(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            server.add_response(b"\x00\x01\x00\x00\x00\x03\x01\x07\x6d")
            mr = dev.read_exception_status()
            assert mr.count == 8
            assert mr.data == b"\x6d"
            assert mr.device_id == 1
            assert mr.function_code == 7
            # 0x6D = 0110 1101
            assert np.array_equal(mr.bits(), [True, False, True, True, False, True, True, False])
            assert np.array_equal(mr.bits("little"), [True, False, True, True, False, True, True, False])
            assert np.array_equal(mr.bits("big"), [False, True, True, False, True, True, False, True])


def test_rtu_read_exception_status() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    server.add_response(b"\x09\x07\x6d\x62\x1f")
    mr = dev.read_exception_status()
    assert mr.count == 8
    assert mr.data == b"\x6d"
    assert mr.device_id == 9
    assert mr.function_code == 7
    # 0x6D = 0110 1101
    assert np.array_equal(mr.bits(), [True, False, True, True, False, True, True, False])
    assert np.array_equal(mr.bits("little"), [True, False, True, True, False, True, True, False])
    assert np.array_equal(mr.bits("big"), [False, True, True, False, True, True, False, True])

    dev.disconnect()


def test_tcp_write_register(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.write_register(55110, 1234, device_id=5)
            assert mr.device_id == 5
            assert mr.function_code == 0x06
            assert mr.data == b"\xd7\x46\x04\xd2"
            assert mr.unpack(">HH") == (55110, 1234)
            assert np.array_equal(mr.array("u2"), (55110, 1234))


def test_rtu_write_register() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()

    mr = dev.write_register(55110, 1234, device_id=5)
    assert mr.device_id == 5
    assert mr.function_code == 0x06
    assert mr.data == b"\xd7\x46\x04\xd2"
    assert mr.unpack(">HH") == (55110, 1234)
    assert np.array_equal(mr.array("u2"), (55110, 1234))

    dev.disconnect()


def test_tcp_write_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.write_registers(55120, [18])
            assert mr.device_id == 1
            assert mr.function_code == 0x10
            # The actual data returned from a Modbus device would only be the first 4 bytes, here it's an echo
            assert mr.data == b"\xd7\x50\x00\x01\x02\x00\x12"

            with pytest.raises(ValueError, match=r"Too many values"):
                _ = dev.write_registers(55120, range(200))

            mr = dev.write_registers(55120, np.array([18], dtype=">u2"))
            assert mr.data == b"\xd7\x50\x00\x01\x02\x00\x12"

            mr = dev.write_registers(55120, (18, 54919))
            assert mr.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"

            with pytest.raises(struct.error):
                _ = dev.write_registers(55120, [70_000])

            mr = dev.write_registers(55120, np.array([18, 54919], dtype=">u2"))
            assert mr.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"

            with pytest.raises(ValueError, match=r"must have a dtype of '>u2', got '<f8'"):
                _ = dev.write_registers(55120, np.array([1854919], dtype="float64"))

            mr = dev.write_registers(55120, Modbus.to_register_values(1234567, dtype="u4"))
            assert mr.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"


def test_rtu_write_registers() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    server.add_response(b"\x01\x10\xd7\x50\x00\x01\x38\x6c")
    mr = dev.write_registers(55120, [18])
    assert mr.device_id == 1
    assert mr.function_code == 0x10
    assert mr.data == b"\xd7\x50\x00\x01"

    with pytest.raises(ValueError, match=r"Too many values"):
        _ = dev.write_registers(55120, range(200))

    server.add_response(b"\x04\x10\xd7\x50\x00\x01\x38\x39")
    mr = dev.write_registers(55120, np.array([18], dtype=">u2"), device_id=4)
    assert mr.device_id == 4
    assert mr.function_code == 0x10
    assert mr.data == b"\xd7\x50\x00\x01"

    server.add_response(b"\x02\x10\x00\x01\x00\x02\x10\x3b")
    mr = dev.write_registers(1, (18, 54919))
    assert mr.device_id == 2
    assert mr.function_code == 0x10
    assert mr.data == b"\x00\x01\x00\x02"

    with pytest.raises(struct.error):
        _ = dev.write_registers(55120, [70_000])

    server.add_response(b"\x02\x10\x00\x01\x00\x02\x10\x3b")
    mr = dev.write_registers(55120, np.array([18, 54919], dtype=">u2"))
    assert mr.device_id == 2
    assert mr.function_code == 0x10
    assert mr.data == b"\x00\x01\x00\x02"

    with pytest.raises(ValueError, match=r"must have a dtype of '>u2', got '<f8'"):
        _ = dev.write_registers(55120, np.array([1854919], dtype="float64"))

    server.add_response(b"\x02\x10\xd7\x50\x00\x02\x78\x5e")
    mr = dev.write_registers(55120, Modbus.to_register_values(1234567, dtype="u4"))
    assert mr.device_id == 2
    assert mr.function_code == 0x10
    assert mr.data == b"\xd7\x50\x00\x02"

    dev.disconnect()


def test_tcp_write_coil(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.write_coil(173, True, device_id=2)  # noqa: FBT003
            assert mr.device_id == 2
            assert mr.function_code == 0x05
            assert mr.data == b"\x00\xad\xff\x00"

            mr = dev.write_coil(2345, False, device_id=20)  # noqa: FBT003
            assert mr.device_id == 20
            assert mr.function_code == 0x05
            assert mr.data == b"\x09\x29\x00\x00"


def test_rtu_write_coil() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()

    mr = dev.write_coil(173, True, device_id=2)  # noqa: FBT003
    assert mr.device_id == 2
    assert mr.function_code == 0x05
    assert mr.data == b"\x00\xad\xff\x00"

    mr = dev.write_coil(2345, False, device_id=20)  # noqa: FBT003
    assert mr.device_id == 20
    assert mr.function_code == 0x05
    assert mr.data == b"\x09\x29\x00\x00"

    dev.disconnect()


def test_tcp_write_coils(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.write_coils(1000, [True], device_id=2)
            assert mr.device_id == 2
            assert mr.function_code == 0x0F
            # The actual data returned from a Modbus device would only be the first 4 bytes, here it's an echo
            assert mr.data == b"\x03\xe8\x00\x01\x01\x01"

            mr = dev.write_coils(2350, [False])
            assert mr.data == b"\x09\x2e\x00\x01\x01\x00"

            mr = dev.write_coils(310, np.array([True, False, False, True, False], dtype=bool))
            assert mr.data == b"\x01\x36\x00\x05\x01\x09"

            mr = dev.write_coils(32000, [True, False, False, True, False, True, False, False])
            assert mr.data == b"\x7d\x00\x00\x08\x01\x29"

            with pytest.raises(ValueError, match=r"must be <= 1968$"):
                _ = dev.write_coils(1, [True] * 2100)

            mr = dev.write_coils(
                23400,
                [
                    True,
                    False,
                    False,
                    False,
                    False,
                    True,
                    False,
                    True,  # 8th
                    False,
                    True,
                    False,
                    False,
                    False,  # 13th (0x0D)
                ],
            )
            assert mr.data == b"\x5b\x68\x00\x0d\x02\xa1\x02"

            mr = dev.write_coils(
                43160,
                [
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    True,  # 8th
                    True,
                    False,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,  # 16th (0x10)
                ],
            )
            assert mr.data == b"\xa8\x98\x00\x10\x02\x81\x05"

            mr = dev.write_coils(
                8620,
                [
                    True,
                    False,
                    False,
                    True,
                    False,
                    False,
                    False,
                    True,  # 8th
                    True,
                    False,
                    True,
                    True,
                    False,
                    False,
                    True,
                    False,  # 16th
                    False,
                    True,
                    True,  # 19th (0x13)
                ],
            )
            assert mr.data == b"\x21\xac\x00\x13\x03\x89\x4d\x06"


def test_rtu_write_coils() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    server.add_response(b"\x02\x0f\x03\xe8\x00\x01\x14\x48")
    mr = dev.write_coils(0, [], device_id=2)
    assert mr.device_id == 2
    assert mr.function_code == 0x0F
    assert mr.data == b"\x03\xe8\x00\x01"

    server.add_response(b"\x01\x0f\x09\x2e\x00\x01\xf7\x9e")
    mr = dev.write_coils(0, [])
    assert mr.data == b"\x09\x2e\x00\x01"

    server.add_response(b"\x01\x0f\x01\x36\x00\x05\x74\x3a")
    mr = dev.write_coils(0, np.array([True, False, False, True, False], dtype=bool))
    assert mr.data == b"\x01\x36\x00\x05"

    server.add_response(b"\x01\x0f\x7d\x00\x00\x08\x4c\x61")
    mr = dev.write_coils(0, [True, False, False, True, False, True, False, False])
    assert mr.data == b"\x7d\x00\x00\x08"

    with pytest.raises(ValueError, match=r"must be <= 1968$"):
        _ = dev.write_coils(1, [True] * 2100)

    server.add_response(b"\x01\x0f\x5b\x68\x00\x0d\x06\xf6")
    mr = dev.write_coils(0, [])
    assert mr.data == b"\x5b\x68\x00\x0d"

    server.add_response(b"\x01\x0f\xa8\x98\x00\x10\xf5\x88")
    mr = dev.write_coils(0, [])
    assert mr.data == b"\xa8\x98\x00\x10"

    server.add_response(b"\x01\x0f\x21\xac\x00\x13\xde\x1b")
    mr = dev.write_coils(0, [])
    assert mr.data == b"\x21\xac\x00\x13"

    dev.disconnect()


def test_tcp_mask_write_register(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.mask_write_register(4, and_mask=0xF2, or_mask=0x25)
            assert mr.data == b"\x00\x04\x00\xf2\x00\x25"
            assert mr.function_code == 0x16
            assert mr.count is None
            assert mr.unpack(">HHH") == (4, 0xF2, 0x25)
            assert np.array_equal(mr.array("uint16"), [4, 0xF2, 0x25])
            assert mr.device_id == 1

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(0, or_mask=70_000)

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(0, and_mask=70_000)

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(70_000)

            mr = dev.mask_write_register(0, device_id=2)
            assert mr.data == b"\x00\x00\xff\xff\x00\x00"
            assert mr.function_code == 0x16
            assert mr.count is None
            assert mr.unpack(">HHH") == (0, 0xFFFF, 0)
            assert np.array_equal(mr.array("uint16"), [0, 0xFFFF, 0])
            assert mr.device_id == 2


def test_rtu_mask_write_register() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()

    mr = dev.mask_write_register(4, and_mask=0xF2, or_mask=0x25)
    assert mr.data == b"\x00\x04\x00\xf2\x00\x25"
    assert mr.function_code == 0x16
    assert mr.count is None
    assert mr.unpack(">HHH") == (4, 0xF2, 0x25)
    assert np.array_equal(mr.array("uint16"), [4, 0xF2, 0x25])
    assert mr.device_id == 1

    with pytest.raises(struct.error):
        _ = dev.mask_write_register(0, or_mask=70_000)

    with pytest.raises(struct.error):
        _ = dev.mask_write_register(0, and_mask=70_000)

    with pytest.raises(struct.error):
        _ = dev.mask_write_register(70_000)

    mr = dev.mask_write_register(0, device_id=2)
    assert mr.data == b"\x00\x00\xff\xff\x00\x00"
    assert mr.function_code == 0x16
    assert mr.count is None
    assert mr.unpack(">HHH") == (0, 0xFFFF, 0)
    assert np.array_equal(mr.array("uint16"), [0, 0xFFFF, 0])
    assert mr.device_id == 2

    dev.disconnect()


def test_tcp_read_write_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            mr = dev.read_write_registers()
            assert mr.count == 0
            assert mr.device_id == 1
            assert mr.function_code == 0x17
            assert mr.data == b"\x00\x00\x00\x00\x00\x00\x00\x00"

            with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
                _ = dev.read_write_registers(read_count=126)

            mr = dev.read_write_registers(read_address=33, read_count=1, write_address=4)
            assert mr.count == 1
            assert mr.device_id == 1
            assert mr.function_code == 0x17
            assert mr.data == b"\x21\x00\x01\x00\x04\x00\x00\x00"

            mr = dev.read_write_registers(address=10, read_count=40, values=1000, device_id=8)
            assert mr.count == 40
            assert mr.device_id == 8
            assert mr.function_code == 0x17
            assert mr.data == b"\x0a\x00\x28\x00\x0a\x00\x01\x02\x03\xe8"

            with pytest.raises(ValueError, match=r"must be <= 121"):
                _ = dev.read_write_registers(values=[1] * 122)

            mr = dev.read_write_registers(read_address=3, read_count=6, write_address=14, values=[1, 2, 3])
            assert mr.count == 6
            assert mr.device_id == 1
            assert mr.function_code == 0x17
            assert mr.data == b"\x03\x00\x06\x00\x0e\x00\x03\x06\x00\x01\x00\x02\x00\x03"

            mr = dev.read_write_registers(
                read_address=3, read_count=6, write_address=14, values=np.array([1, 2, 3], dtype=">u2")
            )
            assert mr.count == 6
            assert mr.device_id == 1
            assert mr.function_code == 0x17
            assert mr.data == b"\x03\x00\x06\x00\x0e\x00\x03\x06\x00\x01\x00\x02\x00\x03"

            with pytest.raises(ValueError, match=r"dtype of '>u2'"):
                _ = dev.read_write_registers(values=np.array([1, 2, 3], dtype="<u2"))

            server.add_response(b"\x00\x06\x00\x00\x00\x0f\x0d\x17\x0c\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff")
            mr = dev.read_write_registers(read_address=3, read_count=6, write_address=14)
            assert mr.count == 6
            assert mr.device_id == 13
            assert mr.function_code == 0x17
            assert mr.data == b"\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff"
            assert np.array_equal(mr.array("uint16"), [254, 2765, 1, 3, 13, 255])


def test_rtu_read_write_registers() -> None:
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    with pytest.raises(ValueError, match=r"must be <= 121"):
        _ = dev.read_write_registers(values=[1] * 122)

    server.add_response(b"\x03\x17\x02\x00\x01\x05\xb4")
    mr = dev.read_write_registers()
    assert mr.count == 0
    assert mr.device_id == 3
    assert mr.function_code == 0x17
    assert mr.data == b"\x00\x01"

    with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
        _ = dev.read_write_registers(read_count=126)

    with pytest.raises(ValueError, match=r"dtype of '>u2'"):
        _ = dev.read_write_registers(values=np.array([1, 2, 3], dtype="<u2"))

    server.add_response(b"\x0d\x17\x0c\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff\x11\x7c")
    mr = dev.read_write_registers(read_address=3, read_count=6, write_address=14)
    assert mr.count == 6
    assert mr.device_id == 13
    assert mr.function_code == 0x17
    assert mr.data == b"\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff"
    assert np.array_equal(mr.array("uint16"), [254, 2765, 1, 3, 13, 255])

    dev.disconnect()


def test_tcp_read_device_identification(tcp_server: type[TCPServer]) -> None:  # noqa: PLR0915
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            server.add_response(
                b"\x00\x01\x00\x00\x00\x1f\x0a\x2b\x0e\x01\x83\x00\x00\x03\x00\x07Vaisala\x01\x06PTU300\x02\x045.16"
            )
            mi = dev.read_device_identification()
            assert mi.device_id == 0x0A
            assert mi.function_code == 0x2B
            assert mi.mei_type == 0x0E
            assert mi.code_id == 0x01
            assert mi.conformity == 0x83
            assert mi.more_follows is False
            assert mi.next_object_id == 0x00
            assert len(mi) == 3
            assert mi[0] == b"Vaisala"
            assert mi[1] == b"PTU300"
            assert mi[2] == b"5.16"
            assert mi.get(3) is None
            with pytest.raises(KeyError, match=r"id 3 is not in the Modbus response"):
                _ = mi[3]
            for o in mi:  # iterable
                assert o.id > -1
                assert isinstance(o.value, bytes)
            assert str(mi) == (
                "ModbusIdentification(code_id=1, conformity=0x83, more_follows=False, next_object_id=0, ids=[0, 1, 2])"
            )
            assert str(mi.objects) == (
                "[ModbusObject(id=0, value=b'Vaisala'),"
                " ModbusObject(id=1, value=b'PTU300'),"
                " ModbusObject(id=2, value=b'5.16')]"
            )

            response = (
                b"\x00\x02\x00\x00\x00\x80\x01\x2b\x0e"
                b"\x02\x81\xff\x04\x05"
                b"\x00\x07Vaisala"
                b"\x01\x06PTU300"
                b"\x02\x045.16"
                b"\x03\x17http://www.vaisala.com/"
                b"\x04FVaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
            )
            server.add_response(response)
            mi = dev.read_device_identification(code_id=2)
            assert mi.device_id == 1
            assert mi.function_code == 0x2B
            assert mi.mei_type == 0x0E
            assert mi.code_id == 2
            assert mi.conformity == 0x81
            assert mi.more_follows is True
            assert mi.next_object_id == 4
            assert len(mi) == 5
            assert mi[0] == b"Vaisala"
            assert mi[1] == b"PTU300"
            assert mi[2] == b"5.16"
            assert mi[3] == b"http://www.vaisala.com/"
            assert mi[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"

            response = (
                b"\x00\x03\x00\x00\x00\xa3\x01\x2b\x0e"
                b"\x03\x83\x00\x00\x08"
                b"\x00\x07Vaisala"
                b"\x01\x06PTU300"
                b"\x02\x045.16"
                b"\x03\x17http://www.vaisala.com/"
                b"\x04FVaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
                b"\x80\x08P4040154"
                b"\x81\n2018-10-04"
                b"\x82\x0bVaisala/HEL"
            )
            server.add_response(response)
            mi = dev.read_device_identification(code_id=3)
            assert mi.device_id == 1
            assert mi.function_code == 0x2B
            assert mi.mei_type == 0x0E
            assert mi.code_id == 3
            assert mi.conformity == 0x83
            assert mi.more_follows is False
            assert mi.next_object_id == 0
            assert len(mi) == 8
            assert mi[0] == b"Vaisala"
            assert mi[1] == b"PTU300"
            assert mi[2] == b"5.16"
            assert mi[3] == b"http://www.vaisala.com/"
            assert mi[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
            assert mi[128] == b"P4040154"
            assert mi[129] == b"2018-10-04"
            assert mi[130] == b"Vaisala/HEL"

            server.add_response(b"\x00\x04\x00\x00\x00\x0d\x01\x2b\x0e\x04\x01\x00\x01\x01\x00\x03ABC")
            mi = dev.read_device_identification(code_id=4)
            assert mi.device_id == 1
            assert mi.function_code == 0x2B
            assert mi.mei_type == 0x0E
            assert mi.code_id == 4
            assert mi.conformity == 1
            assert mi.more_follows is False
            assert mi.next_object_id == 1
            assert len(mi) == 1
            assert mi[0] == b"ABC"

            server.add_response(b"\x00\x05\x00\x00\x00\x12\x09\x2b\x0e\x04\x83\x00\x00\x01\x80\x08P4040154")
            mi = dev.read_device_identification(code_id=4, object_id=128, device_id=9)
            assert mi.device_id == 9
            assert mi.function_code == 0x2B
            assert mi.mei_type == 0x0E
            assert mi.code_id == 4
            assert mi.conformity == 0x83
            assert mi.more_follows is False
            assert mi.next_object_id == 0
            assert len(mi) == 1
            assert mi[128] == b"P4040154"


def test_rtu_read_device_identification() -> None:  # noqa: PLR0915
    dev: Modbus = Connection("Modbus::/mock://").connect()
    server = cast_server(dev)

    server.add_response(b"\x0a\x2b\x0e\x01\x83\x00\x00\x03\x00\x07Vaisala\x01\x06PTU300\x02\x045.16\x90\xb5")
    mi = dev.read_device_identification()
    assert mi.device_id == 0x0A
    assert mi.function_code == 0x2B
    assert mi.mei_type == 0x0E
    assert mi.code_id == 0x01
    assert mi.conformity == 0x83
    assert mi.more_follows is False
    assert mi.next_object_id == 0x00
    assert len(mi) == 3
    assert mi[0] == b"Vaisala"
    assert mi[1] == b"PTU300"
    assert mi[2] == b"5.16"
    assert mi.get(3) is None
    with pytest.raises(KeyError, match=r"id 3 is not in the Modbus response"):
        _ = mi[3]
    for o in mi:  # iterable
        assert o.id > -1
        assert isinstance(o.value, bytes)
    assert str(mi) == (
        "ModbusIdentification(code_id=1, conformity=0x83, more_follows=False, next_object_id=0, ids=[0, 1, 2])"
    )
    assert str(mi.objects) == (
        "[ModbusObject(id=0, value=b'Vaisala'), ModbusObject(id=1, value=b'PTU300'), ModbusObject(id=2, value=b'5.16')]"
    )

    response = (
        b"\x01\x2b\x0e"
        b"\x02\x81\xff\x04\x05"
        b"\x00\x07Vaisala"
        b"\x01\x06PTU300"
        b"\x02\x045.16"
        b"\x03\x17http://www.vaisala.com/"
        b"\x04FVaisala Combined Pressure, Humidity and Temperature Transmitter PTU300\x75\x84"
    )
    server.add_response(response)
    mi = dev.read_device_identification(code_id=2)
    assert mi.device_id == 1
    assert mi.function_code == 0x2B
    assert mi.mei_type == 0x0E
    assert mi.code_id == 2
    assert mi.conformity == 0x81
    assert mi.more_follows is True
    assert mi.next_object_id == 4
    assert len(mi) == 5
    assert mi[0] == b"Vaisala"
    assert mi[1] == b"PTU300"
    assert mi[2] == b"5.16"
    assert mi[3] == b"http://www.vaisala.com/"
    assert mi[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"

    response = (
        b"\x01\x2b\x0e"
        b"\x03\x83\x00\x00\x08"
        b"\x00\x07Vaisala"
        b"\x01\x06PTU300"
        b"\x02\x045.16"
        b"\x03\x17http://www.vaisala.com/"
        b"\x04FVaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
        b"\x80\x08P4040154"
        b"\x81\n2018-10-04"
        b"\x82\x0bVaisala/HEL\xc2\xc4"
    )
    server.add_response(response)
    mi = dev.read_device_identification(code_id=3)
    assert mi.device_id == 1
    assert mi.function_code == 0x2B
    assert mi.mei_type == 0x0E
    assert mi.code_id == 3
    assert mi.conformity == 0x83
    assert mi.more_follows is False
    assert mi.next_object_id == 0
    assert len(mi) == 8
    assert mi[0] == b"Vaisala"
    assert mi[1] == b"PTU300"
    assert mi[2] == b"5.16"
    assert mi[3] == b"http://www.vaisala.com/"
    assert mi[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
    assert mi[128] == b"P4040154"
    assert mi[129] == b"2018-10-04"
    assert mi[130] == b"Vaisala/HEL"

    server.add_response(b"\x01\x2b\x0e\x04\x01\x00\x01\x01\x00\x03ABC\x2d\xb3")
    mi = dev.read_device_identification(code_id=4)
    assert mi.device_id == 1
    assert mi.function_code == 0x2B
    assert mi.mei_type == 0x0E
    assert mi.code_id == 4
    assert mi.conformity == 1
    assert mi.more_follows is False
    assert mi.next_object_id == 1
    assert len(mi) == 1
    assert mi[0] == b"ABC"

    server.add_response(b"\x09\x2b\x0e\x04\x83\x00\x00\x01\x80\x08P4040154\x26\xf1")
    mi = dev.read_device_identification(code_id=4, object_id=128, device_id=9)
    assert mi.device_id == 9
    assert mi.function_code == 0x2B
    assert mi.mei_type == 0x0E
    assert mi.code_id == 4
    assert mi.conformity == 0x83
    assert mi.more_follows is False
    assert mi.next_object_id == 0
    assert len(mi) == 1
    assert mi[128] == b"P4040154"

    dev.disconnect()


def test_ascii_read() -> None:
    dev: Modbus = Connection("Modbus::/mock://::ASCII").connect()
    server = cast_server(dev)

    assert dev.write(0x04, data=b"\x00\xfa\x03\x06\xb7\x09\x0b\x0d\xf0", device_id=0x7B) == 27
    assert server.read() == b":7B0400FA0306B7090B0DF0B6\r\n"

    assert dev.write(0x02, data=b"\xaa\x09\x00\xfa\xf0\x06\xb7\x0d\x0b\x03", device_id=0xCC) == 29
    assert dev.read() == (0xCC, b"\x02\xaa\x09\x00\xfa\xf0\x06\xb7\x0d\x0b\x03")

    dev.disconnect()


def test_ascii_bad_start_frame() -> None:
    dev: Modbus = Connection("Modbus::/mock://::ASCII").connect()
    server = cast_server(dev)

    server.add_response(b"?030201FA\r\n")
    with pytest.raises(MSLConnectionError, match=r"value 0x3F, expected 0x3A"):
        _ = dev.read_coils(1)

    dev.disconnect()


def test_ascii_bad_lrc() -> None:
    dev: Modbus = Connection("Modbus::/mock://::ASCII").connect()
    server = cast_server(dev)

    server.add_response(b":03020100\r\n")
    with pytest.raises(MSLConnectionError, match=r"value 0, expected 250"):
        _ = dev.read_coils(1)

    dev.disconnect()


def test_find_modbus(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"\x00") as server:
        server.add_response(
            b"\x00\x01\x00\x00\x00\x21\x01\x2b\x0e\x01\x83\x00\x00\x03\x00\x08Measure!\x01\x02NZ\x02\t1.2.3dev4"
        )
        devices = find_modbus(ip=[server.host], port=server.port, timeout=0.1)
        assert len(devices) == 1
        assert server.host in devices
        assert devices[server.host].description == "Measure!, NZ, 1.2.3dev4"
        assert devices[server.host].addresses == [f"Modbus::{server.host}"]


def test_find_modbus_identification_not_supported(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"\x00") as server:
        server.add_response(b"\x00\x01\x00\x00\x00\x05\x01\xab\x01")
        devices = find_modbus(ip=[server.host], port=server.port, timeout=0.1)
        assert len(devices) == 1
        assert server.host in devices
        assert devices[server.host].description == "Device identification not available"
        assert devices[server.host].addresses == [f"Modbus::{server.host}"]


@pytest.mark.parametrize(
    "response",
    [
        b"\x00\x01\x00\x00\x00\x05\x01\x09\x08\x07\x06",  # IndexError
        b"\x00\x01\x00\x00\x00\x12\x01\x2b\x0e\x01\x83\x00\x00\x03\x00\x08Me\xa1sure!",  # UnicodeDecodeError
    ],
)
def test_find_modbus_identification_bad_response(tcp_server: type[TCPServer], response: bytes) -> None:
    with tcp_server(term=b"\x00") as server:
        server.add_response(response)
        devices = find_modbus(ip=[server.host], port=server.port, timeout=0.1)
        assert len(devices) == 1
        assert server.host in devices
        assert devices[server.host].description == "Device identification contains invalid data"
        assert devices[server.host].addresses == [f"Modbus::{server.host}"]


def test_find_modbus_identification_timeout(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=b"\x00") as server:
        server.add_response(b"\x00\x01\x00\x00\x00\xff\x00")  # waiting for 0xFF - 1 bytes
        devices = find_modbus(ip=[server.host], port=server.port, timeout=0.1)
        assert len(devices) == 1
        assert server.host in devices
        assert devices[server.host].description == "Device identification not available"
        assert devices[server.host].addresses == [f"Modbus::{server.host}"]


def test_reconnect(tcp_server: type[TCPServer]) -> None:
    server = tcp_server(term=None)
    connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=0.1)

    server.start()
    dev: Modbus = connection.connect()

    mr = dev.read_coils(5130, count=17)
    assert mr.data == b"\n\x00\x11"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x14\n\x00\x11'

    dev.disconnect()

    assert isinstance(dev.interface, Socket)
    assert dev.interface.socket.fileno() == -1

    server.start()
    dev.reconnect()

    assert dev.interface.socket.fileno() != -1

    mr = dev.read_coils(5130, count=17)
    assert mr.data == b"\n\x00\x11"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x14\n\x00\x11'

    dev.disconnect()
    server.stop()

    with pytest.raises(MSLConnectionError):
        dev.reconnect(max_attempts=2)
