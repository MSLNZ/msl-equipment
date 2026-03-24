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


def test_modbus_pdu_str() -> None:
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


def test_modbus_pdu_int16() -> None:
    pdu = ModbusPDU(1, 1, b"\xfc\x18")
    assert pdu.int16() == -1000
    assert pdu.int16("big") == -1000
    assert pdu.int16("little") == 6396


def test_modbus_pdu_uint16() -> None:
    pdu = ModbusPDU(1, 1, bytes([48, 57]))
    assert pdu.uint16() == 12345
    assert pdu.uint16("big") == 12345
    assert pdu.uint16("little") == 14640


def test_modbus_pdu_int32() -> None:
    pdu = ModbusPDU(1, 1, b"\xff\xf0\xbd\xc0")
    assert pdu.int32() == -1_000_000
    assert pdu.int32("big") == -1_000_000
    assert pdu.int32("little") == -1061293825


def test_modbus_pdu_uint32() -> None:
    pdu = ModbusPDU(1, 1, b"\x07[\xcd\x15")
    assert pdu.uint32() == 123456789
    assert pdu.uint32("big") == 123456789
    assert pdu.uint32("little") == 365779719


def test_modbus_pdu_int64() -> None:
    pdu = ModbusPDU(1, 1, b"\xff\xff\xfc\x00\x00\x00\x00\x00")
    assert pdu.int64() == -4398046511104
    assert pdu.int64("big") == -4398046511104
    assert pdu.int64("little") == 16580607


def test_modbus_pdu_uint64() -> None:
    pdu = ModbusPDU(1, 1, b"\x00\x00\x04\x00\x00\x00\x00\x00")
    assert pdu.uint64() == 4398046511104
    assert pdu.uint64("big") == 4398046511104
    assert pdu.uint64("little") == 262144


def test_modbus_pdu_float32() -> None:
    pdu = ModbusPDU(1, 1, b"Dz\x00\x00")
    assert pdu.float32() == 1000.0
    assert pdu.float32("big") == 1000.0
    assert pdu.float32("little") == 4.3860641933366774e-41


def test_modbus_pdu_float64() -> None:
    pdu = ModbusPDU(1, 1, b"\xc12\xc4\xb0\x00\x00\x00\x00")
    assert pdu.float64() == -1.23e6
    assert pdu.float64("big") == -1.23e6
    assert pdu.float64("little") == 1.4652248266e-314


def test_modbus_pdu_nan_inf() -> None:
    pdu = ModbusPDU(1, 1, data=b"\xff\xc0\x00\x00")
    assert np.isnan(pdu.float32())

    pdu = ModbusPDU(1, 1, data=b"\x7f\x80\x00\x00")
    assert np.isinf(pdu.float32())

    pdu = ModbusPDU(1, 1, data=b"\x7f\xf8\x00\x00\x00\x00\x00\x00")
    assert np.isnan(pdu.float64())

    pdu = ModbusPDU(1, 1, data=b"\x7f\xf0\x00\x00\x00\x00\x00\x00")
    assert np.isinf(pdu.float64())


def test_modbus_pdu_decode() -> None:
    pdu = ModbusPDU(1, 1, b"hello")
    assert pdu.decode() == "hello"
    assert pdu.decode("ascii") == "hello"

    with pytest.raises(LookupError):
        _ = pdu.decode("invalid")


def test_modbus_pdu_array_i4() -> None:
    data = np.array([45, -825, 62982, 34104852], dtype=np.int32)
    pdu = ModbusPDU(1, 1, data.tobytes())

    big = np.frombuffer(data.tobytes(), dtype=">i4")
    little = np.frombuffer(data.tobytes(), dtype="<i4")
    assert np.array_equal(pdu.array("i4"), big)
    assert np.array_equal(pdu.array("int32"), big)
    assert np.array_equal(pdu.array(">i4"), big)
    assert np.array_equal(pdu.array("<i4"), little)
    assert np.array_equal(pdu.array(np.int32), big)
    assert np.array_equal(pdu.array(np.dtype(">i4")), big)
    assert np.array_equal(pdu.array(np.dtype("<i4")), little)


def test_modbus_pdu_array_f4() -> None:
    data = b"\x40\xf8\x11\x5f\x40\xd4\x8c\x8a\x40\xb5\xbb\x8a\x40\x90\x78\x9c"
    pdu = ModbusPDU(1, 1, data)

    big = np.frombuffer(data, dtype=">f4")
    little = np.frombuffer(data, dtype="<f4")
    assert np.array_equal(pdu.array("f4"), big)
    assert np.array_equal(pdu.array("float32"), big)
    assert np.array_equal(pdu.array(">f4"), big)
    assert np.array_equal(pdu.array("<f4"), little)
    assert np.array_equal(pdu.array(np.float32), big)
    assert np.array_equal(pdu.array(np.dtype(">f4")), big)
    assert np.array_equal(pdu.array(np.dtype("<f4")), little)


def test_modbus_pdu_array_f8() -> None:
    data = b"\x40\xf8\x11\x5f\x40\xd4\x8c\x8a\x40\xb5\xbb\x8a\x40\x90\x78\x9c"
    pdu = ModbusPDU(1, 1, data)

    big = np.frombuffer(data, dtype=">f8")
    little = np.frombuffer(data, dtype="<f8")
    assert np.array_equal(pdu.array("f8"), big)
    assert np.array_equal(pdu.array("float64"), big)
    assert np.array_equal(pdu.array(">f8"), big)
    assert np.array_equal(pdu.array("<f8"), little)
    assert np.array_equal(pdu.array(np.float64), big)
    assert np.array_equal(pdu.array(float), big)
    assert np.array_equal(pdu.array(np.dtype(">f8")), big)
    assert np.array_equal(pdu.array(np.dtype("<f8")), little)


def test_modbus_pdu_bits() -> None:
    pdu = ModbusPDU(1, 1, b"\x01")
    assert np.array_equal(pdu.bits(), [True, False, False, False, False, False, False, False])
    assert np.array_equal(pdu.bits("big"), [False, False, False, False, False, False, False, True])

    pdu = ModbusPDU(1, 1, b"\x01", count=1)
    assert np.array_equal(pdu.bits(), [True])
    assert np.array_equal(pdu.bits("big"), [False])

    pdu = ModbusPDU(1, 1, 0b0110_0001.to_bytes(1, "big"), count=7)
    assert np.array_equal(pdu.bits(), [True, False, False, False, False, True, True])
    assert np.array_equal(pdu.bits("big"), [False, True, True, False, False, False, False])

    pdu = ModbusPDU(1, 1, 0b0110_0001.to_bytes(1, "big"), count=8)
    assert np.array_equal(pdu.bits(), [True, False, False, False, False, True, True, False])
    assert np.array_equal(pdu.bits("big"), [False, True, True, False, False, False, False, True])


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


def test_tcp_read_coils(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"2001 coils, maximum allowed is 2000"):
                _ = dev.read_coils(1, count=2001)

            pdu = dev.read_coils(5130, count=17, device_id=240)
            assert pdu.data == b"\n\x00\x11"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x14\n\x00\x11'
            assert pdu.count == 17
            assert pdu.device_id == 240
            assert pdu.function_code == 1

            # Response from MODBUS Application Protocol Specification V1.1b3
            server.add_response(b"\x00\x02\x00\x00\x00\x06\xf0\x01\x03\xcd\x6b\x05")
            pdu = dev.read_coils(0, count=8 + 8 + 3)  # address ignored
            assert pdu.data == b"\xcd\x6b\x05"
            assert pdu.count == 19
            assert pdu.device_id == 240  # \xF0
            assert pdu.function_code == 1
            # fmt: off
            # 1  1  0  0  1  1  0  1   0  1  1  0  1  0  1  1   0 0 0 0 0 1  0  1
            # 27 26 25 24 23 22 21 20  35 34 33 32 31 30 29 28  X X X X X 38 37 36
            assert np.array_equal(pdu.bits(), [
                # 20     21    22    23     24     25    26    27    28    29     30    31     32    33    34     35    36     37    38  # noqa: E501
                True, False, True, True, False, False, True, True, True, True, False, True, False, True, True, False, True, False, True  # noqa: E501
            ])
            # fmt: on

            server.add_response(b"\x00\x03\x00\x00\x00\x04\xf0\x01\x01\x01")
            pdu = dev.read_coils(0)  # address ignored
            assert pdu.data == b"\x01"
            assert pdu.count == 1
            assert pdu.device_id == 240  # \xF0
            assert pdu.function_code == 1
            assert np.array_equal(pdu.bits(), [True])
            assert np.array_equal(pdu.bits("big"), [False])
            pdu.count = None
            assert np.array_equal(pdu.bits(), [True, False, False, False, False, False, False, False])
            assert np.array_equal(pdu.bits("big"), [False, False, False, False, False, False, False, True])

            server.add_response(b"\x00\x03\x00\x00\x00\x03\x01\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 3, expected 4$"):
                _ = dev.read_coils(0)

            server.add_response(b"\x00\x05\x00\x00\x00\x04\x01\x02\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x01$"):
                _ = dev.read_coils(0)

            # https://github.com/pymodbus-dev/pymodbus/issues/2630
            server.add_response(b"\x00\x06\x00\x00\x00\x05\xf1\x01\x02\xf5\xff")
            pdu = dev.read_coils(0, count=16)  # address ignored
            assert pdu.data == b"\xf5\xff"
            assert pdu.count == 16
            assert pdu.device_id == 241  # \xF1
            assert pdu.function_code == 1
            assert np.array_equal(
                pdu.bits(),
                [True, False, True, False, True, True, True, True, True, True, True, True, True, True, True, True],
            )

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readCoils
            server.add_response(b"\x00\x07\x00\x00\x00\x05\x02\x01\x02\x80\x02")
            pdu = dev.read_coils(0, count=12)  # address ignored
            assert pdu.data == b"\x80\x02"
            assert pdu.count == 12
            assert pdu.device_id == 2
            assert pdu.function_code == 1
            assert np.array_equal(
                #      33     34     35     36     37     38     39    40     41    42     43     44
                [False, False, False, False, False, False, False, True, False, True, False, False],
                pdu.bits(),
            )


def test_tcp_read_discrete_inputs(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"2001 discrete inputs, maximum allowed is 2000"):
                _ = dev.read_discrete_inputs(1, count=2001)

            pdu = dev.read_discrete_inputs(1020, count=10, device_id=31)
            assert pdu.data == b"\xfc\x00\n"  # last 3 bytes of struct.pack(">HH", 5130, 17) == b'\x03\xfc\x00\n'
            assert pdu.count == 10
            assert pdu.device_id == 31
            assert pdu.function_code == 2

            # Response from MODBUS Application Protocol Specification V1.1b3
            server.add_response(b"\x00\x02\x00\x00\x00\x06\x04\x02\x03\xac\xdb\x35")
            pdu = dev.read_discrete_inputs(0, count=8 + 8 + 6)  # address ignored
            assert pdu.data == b"\xac\xdb\x35"
            assert pdu.count == 22
            assert pdu.device_id == 4
            assert pdu.function_code == 2
            # fmt: off
            #   1   0   1   0   1   1   0   0    1   1   0   1   1   0   1   1  0 0   1   1   0   1   0   1
            # 204 203 202 201 200 199 198 197  212 211 210 209 208 207 206 205  X X 218 217 216 215 214 213
            assert np.array_equal(pdu.bits(), [
                # 197    198   199   200    201   202    203   204   205   206    207   208   209    210   211   212   213    214   215    216   217   218  # noqa: E501
                False, False, True, True, False, True, False, True, True, True, False, True, True, False, True, True, True, False, True, False, True, True  # noqa: E501
            ])
            # fmt: on

            server.add_response(b"\x00\x03\x00\x00\x00\x04\xf0\x02\x01\x01")
            pdu = dev.read_discrete_inputs(0)  # address ignored
            assert pdu.data == b"\x01"
            assert pdu.count == 1
            assert pdu.device_id == 240  # \xF0
            assert pdu.function_code == 2
            assert np.array_equal(pdu.bits(), [True])
            assert np.array_equal(pdu.bits("big"), [False])
            pdu.count = None
            assert np.array_equal(pdu.bits(), [True, False, False, False, False, False, False, False])
            assert np.array_equal(pdu.bits("big"), [False, False, False, False, False, False, False, True])

            server.add_response(b"\x00\x01\x00\x00\x00\x03\x02\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 4$"):
                _ = dev.read_discrete_inputs(0)

            server.add_response(b"\x00\x05\x00\x00\x00\x04\x01\x05\x01\x01")
            with pytest.raises(MSLConnectionError, match=r"function code 0x05, expected 0x02$"):
                _ = dev.read_discrete_inputs(0)

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readInputs
            server.add_response(b"\x00\x06\x00\x00\x00\x05\x08\x02\x02\x05\x00")
            pdu = dev.read_discrete_inputs(0, count=16)  # address ignored
            assert pdu.data == b"\x05\x00"
            assert pdu.count == 16
            assert pdu.device_id == 8
            assert pdu.function_code == 2
            assert np.array_equal(pdu.bits(), [True, False, True] + [False] * 13)


def test_tcp_read_holding_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
                _ = dev.read_holding_registers(1, count=126)

            server.add_response(b"\x00\x01\x00\x00\x00\x09\x02\x03\x06\x02\x2b\x00\x00\x00\x64")
            pdu = dev.read_holding_registers(0, count=3)
            assert pdu.count == 3
            assert pdu.data == b"\x02\x2b\x00\x00\x00\x64"
            assert pdu.device_id == 2
            assert pdu.function_code == 3
            assert np.array_equal(pdu.array("u2"), [555, 0, 100])

            server.add_response(b"\x00\x01\x00\x00\x00\x07\x01\x03\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"transaction ID 1, expected 2$"):
                _ = dev.read_holding_registers(0)

            server.add_response(b"\x00\x03\x00\x00\x00\x07\x01\x02\x04\x00\x11\x22\x33")
            with pytest.raises(MSLConnectionError, match=r"function code 0x02, expected 0x03$"):
                _ = dev.read_holding_registers(0)

            server.add_response(b"\x00\x04\x00\x00\x00\x05\x01\x03\x02\xa0\x11")
            pdu = dev.read_holding_registers(0, count=1)
            assert pdu.count == 1
            assert pdu.data == b"\xa0\x11"
            assert pdu.device_id == 1
            assert pdu.function_code == 3
            assert pdu.uint16() == 40977

            # https://www.fernhillsoftware.com/help/drivers/modbus/modbus-protocol.html#readHoldingRegs
            server.add_response(b"\x00\x05\x00\x00\x00\x07\x01\x03\x04\x03\xe8\x13\x88")
            pdu = dev.read_holding_registers(0, count=2)
            assert pdu.count == 2
            assert pdu.data == b"\x03\xe8\x13\x88"
            assert pdu.device_id == 1
            assert pdu.function_code == 3
            assert np.array_equal(pdu.array("uint16"), [1000, 5000])


def test_tcp_read_input_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            with pytest.raises(ValueError, match=r"input registers, maximum allowed is 125"):
                _ = dev.read_input_registers(1, count=126)

            server.add_response(b"\x00\x01\x00\x00\x00\x05\x01\x04\x02\x00\x11")
            pdu = dev.read_input_registers(55100)
            assert pdu.count == 1
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
            assert pdu.count == 2
            assert pdu.data == b"\x00\x11\x22\x33"
            assert pdu.device_id == 1
            assert pdu.function_code == 4
            assert pdu.uint32() == 1122867


def test_tcp_read_exception_status(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            server.add_response(b"\x00\x01\x00\x00\x00\x03\x01\x07\x6d")
            pdu = dev.read_exception_status()
            assert pdu.count == 8
            assert pdu.data == b"\x6d"
            assert pdu.device_id == 1
            assert pdu.function_code == 7
            # 0x6D = 0110 1101
            assert np.array_equal(pdu.bits(), [True, False, True, True, False, True, True, False])
            assert np.array_equal(pdu.bits("little"), [True, False, True, True, False, True, True, False])
            assert np.array_equal(pdu.bits("big"), [False, True, True, False, True, True, False, True])


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


def test_tcp_mask_write_register(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.mask_write_register(4, and_mask=0xF2, or_mask=0x25)
            assert pdu.data == b"\x00\x04\x00\xf2\x00\x25"
            assert pdu.function_code == 0x16
            assert pdu.count is None
            assert pdu.unpack(">HHH") == (4, 0xF2, 0x25)
            assert np.array_equal(pdu.array("uint16"), [4, 0xF2, 0x25])
            assert pdu.device_id == 1

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(0, or_mask=70_000)

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(0, and_mask=70_000)

            with pytest.raises(struct.error):
                _ = dev.mask_write_register(70_000)

            pdu = dev.mask_write_register(0, device_id=2)
            assert pdu.data == b"\x00\x00\xff\xff\x00\x00"
            assert pdu.function_code == 0x16
            assert pdu.count is None
            assert pdu.unpack(">HHH") == (0, 0xFFFF, 0)
            assert np.array_equal(pdu.array("uint16"), [0, 0xFFFF, 0])
            assert pdu.device_id == 2


def test_tcp_readwrite_registers(tcp_server: type[TCPServer]) -> None:
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            pdu = dev.read_write_registers()
            assert pdu.count == 0
            assert pdu.device_id == 1
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x00\x00\x00\x00\x00\x00\x00\x00"

            with pytest.raises(ValueError, match=r"holding registers, maximum allowed is 125"):
                _ = dev.read_write_registers(read_count=126)

            pdu = dev.read_write_registers(read_address=33, read_count=1, write_address=4)
            assert pdu.count == 1
            assert pdu.device_id == 1
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x21\x00\x01\x00\x04\x00\x00\x00"

            pdu = dev.read_write_registers(address=10, read_count=40, values=1000, device_id=8)
            assert pdu.count == 40
            assert pdu.device_id == 8
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x0a\x00\x28\x00\x0a\x00\x01\x02\x03\xe8"

            with pytest.raises(ValueError, match=r"must be <= 121"):
                _ = dev.read_write_registers(values=[1] * 122)

            pdu = dev.read_write_registers(read_address=3, read_count=6, write_address=14, values=[1, 2, 3])
            assert pdu.count == 6
            assert pdu.device_id == 1
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x03\x00\x06\x00\x0e\x00\x03\x06\x00\x01\x00\x02\x00\x03"

            pdu = dev.read_write_registers(
                read_address=3, read_count=6, write_address=14, values=np.array([1, 2, 3], dtype=">u2")
            )
            assert pdu.count == 6
            assert pdu.device_id == 1
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x03\x00\x06\x00\x0e\x00\x03\x06\x00\x01\x00\x02\x00\x03"

            with pytest.raises(ValueError, match=r"dtype of '>u2'"):
                _ = dev.read_write_registers(values=np.array([1, 2, 3], dtype="<u2"))

            server.add_response(b"\x00\x06\x00\x00\x00\x0f\x0d\x17\x0c\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff")
            pdu = dev.read_write_registers(read_address=3, read_count=6, write_address=14)
            assert pdu.count == 6
            assert pdu.device_id == 13
            assert pdu.function_code == 0x17
            assert pdu.data == b"\x00\xfe\x0a\xcd\x00\x01\x00\x03\x00\x0d\x00\xff"
            assert np.array_equal(pdu.array("uint16"), [254, 2765, 1, 3, 13, 255])


def test_tcp_read_device_identification(tcp_server: type[TCPServer]) -> None:  # noqa: PLR0915
    with tcp_server(term=None) as server:
        connection = Connection(f"Modbus::{server.host}::{server.port}", timeout=1)

        dev: Modbus
        with connection.connect() as dev:
            server.add_response(
                b"\x00\x01\x00\x00\x00\x1f\x0a\x2b\x0e\x01\x83\x00\x00\x03\x00\x07Vaisala\x01\x06PTU300\x02\x045.16"
            )
            pdu = dev.read_device_identification()
            assert pdu.device_id == 0x0A
            assert pdu.function_code == 0x2B
            assert pdu.mei_type == 0x0E
            assert pdu.code_id == 0x01
            assert pdu.conformity == 0x83
            assert pdu.more_follows is False
            assert pdu.next_object_id == 0x00
            assert len(pdu) == 3
            assert pdu[0] == b"Vaisala"
            assert pdu[1] == b"PTU300"
            assert pdu[2] == b"5.16"
            assert pdu.get(3) is None
            with pytest.raises(KeyError, match=r"id 3 is not in the Modbus response"):
                _ = pdu[3]
            for o in pdu:  # iterable
                assert o.id > -1
                assert isinstance(o.value, bytes)
            assert str(pdu) == (
                "ModbusIdentification(code_id=1, conformity=0x83, more_follows=False, next_object_id=0, ids=[0, 1, 2])"
            )
            assert str(pdu.objects) == (
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
            pdu = dev.read_device_identification(code_id=2)
            assert pdu.device_id == 1
            assert pdu.function_code == 0x2B
            assert pdu.mei_type == 0x0E
            assert pdu.code_id == 2
            assert pdu.conformity == 0x81
            assert pdu.more_follows is True
            assert pdu.next_object_id == 4
            assert len(pdu) == 5
            assert pdu[0] == b"Vaisala"
            assert pdu[1] == b"PTU300"
            assert pdu[2] == b"5.16"
            assert pdu[3] == b"http://www.vaisala.com/"
            assert pdu[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"

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
            pdu = dev.read_device_identification(code_id=3)
            assert pdu.device_id == 1
            assert pdu.function_code == 0x2B
            assert pdu.mei_type == 0x0E
            assert pdu.code_id == 3
            assert pdu.conformity == 0x83
            assert pdu.more_follows is False
            assert pdu.next_object_id == 0
            assert len(pdu) == 8
            assert pdu[0] == b"Vaisala"
            assert pdu[1] == b"PTU300"
            assert pdu[2] == b"5.16"
            assert pdu[3] == b"http://www.vaisala.com/"
            assert pdu[4] == b"Vaisala Combined Pressure, Humidity and Temperature Transmitter PTU300"
            assert pdu[128] == b"P4040154"
            assert pdu[129] == b"2018-10-04"
            assert pdu[130] == b"Vaisala/HEL"

            server.add_response(b"\x00\x04\x00\x00\x00\x0d\x01\x2b\x0e\x04\x01\x00\x01\x01\x00\x03ABC")
            pdu = dev.read_device_identification(code_id=4)
            assert pdu.device_id == 1
            assert pdu.function_code == 0x2B
            assert pdu.mei_type == 0x0E
            assert pdu.code_id == 4
            assert pdu.conformity == 1
            assert pdu.more_follows is False
            assert pdu.next_object_id == 1
            assert len(pdu) == 1
            assert pdu[0] == b"ABC"

            server.add_response(b"\x00\x05\x00\x00\x00\x12\x09\x2b\x0e\x04\x83\x00\x00\x01\x80\x08P4040154")
            pdu = dev.read_device_identification(code_id=4, object_id=128, device_id=9)
            assert pdu.device_id == 9
            assert pdu.function_code == 0x2B
            assert pdu.mei_type == 0x0E
            assert pdu.code_id == 4
            assert pdu.conformity == 0x83
            assert pdu.more_follows is False
            assert pdu.next_object_id == 0
            assert len(pdu) == 1
            assert pdu[128] == b"P4040154"
