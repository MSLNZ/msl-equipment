from __future__ import annotations

import struct
from typing import TYPE_CHECKING

import numpy as np
import pytest

from msl.equipment import Connection, Equipment, Modbus, MSLConnectionError
from msl.equipment.interfaces.modbus import (
    FramerType,
    ModbusPDU,
    ParsedModbusAddress,
    SocketFramer,
    parse_modbus_address,
)

if TYPE_CHECKING:
    from tests.conftest import TCPServer, UDPServer


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
        ("MODBUS::/dev/ttyS0", ParsedModbusAddress(address="/dev/ttyS0", framer=FramerType.RTU)),
        ("MODBUS::/dev/1.2::rtu", ParsedModbusAddress(address="/dev/1.2", framer=FramerType.RTU)),
        ("MODBUS::/dev/1.2::ASCII", ParsedModbusAddress(address="/dev/1.2", framer=FramerType.ASCII)),
        ("MODBUS::/dev/1.2::UDP", ParsedModbusAddress(address="/dev/1.2", framer=FramerType.RTU)),  # UDP ignored
        ("MODBUS::1.2.3.4", ParsedModbusAddress(address="TCP::1.2.3.4::502", framer=FramerType.SOCKET)),
        ("MODBUS::1.2.3.4::1", ParsedModbusAddress(address="TCP::1.2.3.4::1", framer=FramerType.SOCKET)),
        ("MODBUS::abc::621::AscII", ParsedModbusAddress(address="TCP::abc::621", framer=FramerType.ASCII)),
        ("MODBUS::a::621::rtu", ParsedModbusAddress(address="TCP::a::621", framer=FramerType.RTU)),
        ("MODBUS::ASCII", ParsedModbusAddress(address="TCP::ASCII::502", framer=FramerType.SOCKET)),
        ("MODBUS::rtu::rtu", ParsedModbusAddress(address="TCP::rtu::502", framer=FramerType.RTU)),
        (
            "MODBUS::company.com::1234::SOCKET",
            ParsedModbusAddress(address="TCP::company.com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::company.com::1234::SOCKET::UDP",
            ParsedModbusAddress(address="UDP::company.com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::company.com::1234::UDP",
            ParsedModbusAddress(address="UDP::company.com::1234", framer=FramerType.SOCKET),
        ),
        (
            "MODBUS::192.168.1.100::UDP",
            ParsedModbusAddress(address="UDP::192.168.1.100::502", framer=FramerType.SOCKET),
        ),
    ],
)
def test_parse_address_valid(address: str, expected: ParsedModbusAddress) -> None:
    assert parse_modbus_address(address) == expected


def test_modbus_pdu() -> None:
    pdu = ModbusPDU(1, 2, b"")
    assert pdu.data == b""
    assert pdu.device_id == 1
    assert pdu.function_code == 2
    assert str(pdu) == "ModbusPDU(device_id=1, function_code=0x02, data=b'')"

    pdu = ModbusPDU(200, 10, b"Hello")
    assert pdu.data == b"Hello"
    assert pdu.device_id == 200
    assert pdu.function_code == 10
    assert str(pdu) == "ModbusPDU(device_id=200, function_code=0x0A, data=b'Hello')"

    expected = -1000
    pdu = ModbusPDU(1, 1, expected.to_bytes(2, "big", signed=True))
    assert pdu.int16() == expected

    expected = 12345
    pdu = ModbusPDU(1, 1, expected.to_bytes(2, "big"))
    assert pdu.uint16() == expected

    expected = -1_000_000
    pdu = ModbusPDU(1, 1, expected.to_bytes(4, "big", signed=True))
    assert pdu.int32() == expected

    expected = 123456789
    pdu = ModbusPDU(1, 1, expected.to_bytes(4, "big"))
    assert pdu.uint32() == expected

    expected = -1 << 42
    pdu = ModbusPDU(1, 1, expected.to_bytes(8, "big", signed=True))
    assert pdu.int64() == expected

    expected = 1 << 42
    pdu = ModbusPDU(1, 1, expected.to_bytes(8, "big"))
    assert pdu.uint64() == expected

    pdu = ModbusPDU(1, 1, b"Dz\x00\x00")
    assert pdu.float32() == 1000.0

    pdu = ModbusPDU(1, 1, b"\xc12\xc4\xb0\x00\x00\x00\x00")
    assert pdu.float64() == -1.23e6

    pdu = ModbusPDU(1, 1, b"hello")
    assert pdu.decode() == "hello"

    data = b"\x40\xf8\x11\x5f\x40\xd4\x8c\x8a\x40\xb5\xbb\x8a\x40\x90\x78\x9c"
    expected_array = np.array([7.7521205, 6.6421556, 5.679143, 4.514723], dtype=">f4")
    pdu = ModbusPDU(1, 1, data)
    assert np.array_equal(pdu.array(">f4"), expected_array)
    assert np.array_equal(pdu.array("<f4"), expected_array)
    assert np.array_equal(pdu.array("f4"), expected_array)
    assert np.array_equal(pdu.array(np.float32), expected_array)


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


def test_invalid_modbus_address() -> None:
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


def test_modbus_exception_code(tcp_server: type[TCPServer]) -> None:
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


def test_tcp_read_input_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            server.add_response(b"\x00\x01\x00\x00\x00\x05\x01\x04\x02\x00\x11")
            pdu = dev.read_input_registers(55100)
            assert pdu.data == b"\x00\x11"
            assert pdu.device_id == 1
            assert pdu.function_code == 4
            assert pdu.uint16() == 17

            server.add_response(b"\x00\x01\x00\x00\x00\x07\x01\x04\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 2$"):
                _ = dev.read_input_registers(55100)

            server.add_response(b"\x00\x03\x00\x00\x00\x07\x01\x02\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x04$"):
                _ = dev.read_input_registers(55100)

            server.add_response(b"\x00\x04\x00\x00\x00\x07\x01\x04\x04\x00\x11\x22\x33")
            pdu = dev.read_input_registers(55100, count=2)
            assert pdu.data == b"\x00\x11\x22\x33"
            assert pdu.device_id == 1
            assert pdu.function_code == 4
            assert pdu.uint32() == 1122867


def test_tcp_write_register(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.write_register(55110, 1234, device_id=5)
            assert pdu.device_id == 5
            assert pdu.function_code == 0x06
            assert pdu.data == b"\xd7\x46\x04\xd2"
            assert pdu.unpack(">HH") == (55110, 1234)
            assert np.array_equal(pdu.array("u2"), (55110, 1234))


def test_tcp_write_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.write_registers(55120, [18])
            assert pdu.device_id == 1
            assert pdu.function_code == 0x10
            # The actual data returned from a Modbus device would only be the first 4 bytes, here it's an echo
            assert pdu.data == b"\xd7\x50\x00\x01\x02\x00\x12"

            with pytest.raises(ValueError, match=r"Too many values"):
                _ = dev.write_registers(55120, range(200))

            pdu = dev.write_registers(55120, np.array([18], dtype=">u2"))
            assert pdu.data == b"\xd7\x50\x00\x01\x02\x00\x12"

            pdu = dev.write_registers(55120, (18, 54919))
            assert pdu.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"

            with pytest.raises(struct.error):
                _ = dev.write_registers(55120, [70_000])

            pdu = dev.write_registers(55120, np.array([18, 54919], dtype=">u2"))
            assert pdu.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"

            with pytest.raises(ValueError, match=r"must have a dtype of '>u2', got '<f8'"):
                _ = dev.write_registers(55120, np.array([1854919], dtype="float64"))

            pdu = dev.write_registers(55120, Modbus.to_register_values(1234567, dtype="u4"))
            assert pdu.data == b"\xd7\x50\x00\x02\x04\x00\x12\xd6\x87"


def test_tcp_write_coil(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.write_coil(173, True, device_id=2)  # noqa: FBT003
            assert pdu.device_id == 2
            assert pdu.function_code == 0x05
            assert pdu.data == b"\x00\xad\xff\x00"

            pdu = dev.write_coil(2345, False, device_id=20)  # noqa: FBT003
            assert pdu.device_id == 20
            assert pdu.function_code == 0x05
            assert pdu.data == b"\x09\x29\x00\x00"


def test_tcp_write_coils(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.write_coils(1000, [True], device_id=2)
            assert pdu.device_id == 2
            assert pdu.function_code == 0x0F
            # The actual data returned from a Modbus device would only be the first 4 bytes, here it's an echo
            assert pdu.data == b"\x03\xe8\x00\x01\x01\x01"

            pdu = dev.write_coils(2350, [False])
            assert pdu.data == b"\x09\x2e\x00\x01\x01\x00"

            pdu = dev.write_coils(310, np.array([True, False, False, True, False], dtype=bool))
            assert pdu.data == b"\x01\x36\x00\x05\x01\x09"

            pdu = dev.write_coils(32000, [True, False, False, True, False, True, False, False])
            assert pdu.data == b"\x7d\x00\x00\x08\x01\x29"

            with pytest.raises(ValueError, match=r"must be <= 1968$"):
                _ = dev.write_coils(1, [True] * 2100)

            pdu = dev.write_coils(
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
            assert pdu.data == b"\x5b\x68\x00\x0d\x02\xa1\x02"

            pdu = dev.write_coils(
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
            assert pdu.data == b"\xa8\x98\x00\x10\x02\x81\x05"

            pdu = dev.write_coils(
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
            assert pdu.data == b"\x21\xac\x00\x13\x03\x89\x4d\x06"
