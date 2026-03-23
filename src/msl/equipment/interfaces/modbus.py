"""Base class for the Modbus protocol."""

# cSpell: ignore HHHB HHHHB unpackbits
from __future__ import annotations

import re
from enum import Enum
from struct import pack, unpack
from typing import TYPE_CHECKING, NamedTuple

import numpy as np

from msl.equipment.schema import Connection, Interface

from .message_based import MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, Literal

    from numpy.typing import DTypeLike, NDArray

    from msl.equipment.schema import Equipment

    from .message_based import MessageBased


REGEX = re.compile(
    r"^MODBUS::((?P<dev>/dev/[^\s:]+)|(?P<com>COM\d+)|(?P<host>[^\s:]+)(::(?P<port>\d+))?)(::(?P<framer>(ASCII|RTU|SOCKET))?)?(?P<udp>::UDP)?$",
    flags=re.IGNORECASE,
)


class Modbus(Interface, regex=REGEX):
    """Base class for the Modbus protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for the Modbus protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the same _properties_
        as either [Serial][msl.equipment.interfaces.serial.Serial] or [Socket][msl.equipment.interfaces.socket.Socket],
        depending on which underlying interface is used for the connection.
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        parsed = parse_modbus_address(equipment.connection.address)
        if parsed is None:
            msg = f"Invalid Modbus address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._repr: str = self._str[:-1] + f" at {parsed.address}>"

        c = Connection(parsed.address, properties=equipment.connection.properties)
        try:
            interface: MessageBased = c.connect()
        except (MSLConnectionError, MSLTimeoutError) as e:
            raise MSLConnectionError(self, e.message) from None

        interface._str = self._str  # noqa: SLF001
        interface._repr = self._repr  # noqa: SLF001
        interface.read_termination = None
        interface.write_termination = None

        self._framer: Framer
        if parsed.framer == FramerType.SOCKET:
            self._framer = SocketFramer(interface)
        else:
            msg = "Only SOCKET frames are currently supported"
            raise MSLConnectionError(self, msg)

    def _check_function_code(self, function_code: int, pdu: ModbusPDU) -> None:
        if pdu.function_code != function_code:
            msg = f"Received unexpected Modbus function code 0x{pdu.function_code:02X}, expected 0x{function_code:02X}"
            raise MSLConnectionError(self._framer.interface, msg)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the Modbus equipment."""
        if hasattr(self, "_framer"):
            self._framer.disconnect()
            super().disconnect()

    def mask_write_register(
        self, address: int, *, and_mask: int = 65535, or_mask: int = 0, device_id: int = 1
    ) -> ModbusPDU:
        """Mask Write Register (function code `0x016`).

        Modifies the contents of the specified holding-register address using a combination of an AND mask,
        an OR mask, and the register's current contents. This method can be used to set or clear individual
        bits in the holding register.

        Args:
            address: Holding register address. Must be in the range [0, 65535].
            and_mask: The AND bitmask to apply to the register address. Must be in the range [0, 65535].
            or_mask: The OR bitmask to apply to the register address. Must be in the range [0, 65535].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response. The response data is the result after
                the register masks have been written.
        """
        function_code = 0x16
        _ = self.write(function_code, data=pack(">HHH", address, and_mask, or_mask), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[1:])
        self._check_function_code(function_code, pdu)
        return pdu

    def read(self) -> tuple[int, bytes]:
        """Read a Modbus message.

        Returns:
            The Modbus device ID and the Protocol Data Unit of the response, i.e., `(ID, PDU)`.
        """
        device_id, pdu = self._framer.read()
        if pdu[0] <= 0x80:  # noqa: PLR2004
            return device_id, pdu

        # Consider handling exception code 5 and 6 differently (don't raise an error)
        msg = EXCEPTIONS.get(pdu[1], f"Unknown Modbus exception code 0x{pdu[1]:02X}")
        raise MSLConnectionError(self, msg)

    def read_coils(self, address: int, *, count: int = 1, device_id: int = 1) -> ModbusPDU:
        """Read coils (function code `0x01`).

        Args:
            address: Starting register address to read from. Must be in the range [0, 65535].
            count: The number of coils to read. Must be in the range [1, 2000].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response. Call the
                [bits][msl.equipment.interfaces.modbus.ModbusPDU.bits] method to get the
                ON/OFF state of each coil.
        """
        if count > 2000:  # noqa: PLR2004
            msg = f"Requesting to read {count} coils, maximum allowed is 2000"
            raise ValueError(msg)

        function_code = 0x01
        _ = self.write(function_code, data=pack(">HH", address, count), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[2:], count=count)
        self._check_function_code(function_code, pdu)
        return pdu

    def read_discrete_inputs(self, address: int, *, count: int = 1, device_id: int = 1) -> ModbusPDU:
        """Read discrete inputs (function code `0x02`).

        Args:
            address: Starting register address to read from. Must be in the range [0, 65535].
            count: The number of discrete inputs to read. Must be in the range [1, 2000].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response. Call the
                [bits][msl.equipment.interfaces.modbus.ModbusPDU.bits] method to get the
                ON/OFF state of each discrete input.
        """
        if count > 2000:  # noqa: PLR2004
            msg = f"Requesting to read {count} discrete inputs, maximum allowed is 2000"
            raise ValueError(msg)

        function_code = 0x02
        _ = self.write(function_code, data=pack(">HH", address, count), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[2:], count=count)
        self._check_function_code(function_code, pdu)
        return pdu

    def read_holding_registers(self, address: int, *, count: int = 1, device_id: int = 1) -> ModbusPDU:
        """Read holding registers (function code `0x03`).

        Args:
            address: Starting register address to read from. Must be in the range [0, 65535].
            count: The number of 16-bit registers to read. Must be in the range [1, 125].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response.
        """
        if count > 125:  # noqa: PLR2004
            msg = f"Requesting to read {count} holding registers, maximum allowed is 125"
            raise ValueError(msg)

        function_code = 0x03
        _ = self.write(function_code, data=pack(">HH", address, count), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[2:], count=count)
        self._check_function_code(function_code, pdu)
        return pdu

    def read_input_registers(self, address: int, *, count: int = 1, device_id: int = 1) -> ModbusPDU:
        """Read input registers (function code `0x04`).

        Args:
            address: Starting register address to read from. Must be in the range [0, 65535].
            count: The number of 16-bit registers to read. Must be in the range [1, 125].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response.
        """
        if count > 125:  # noqa: PLR2004
            msg = f"Requesting to read {count} input registers, maximum allowed is 125"
            raise ValueError(msg)

        function_code = 0x04
        _ = self.write(function_code, data=pack(">HH", address, count), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[2:], count=count)
        self._check_function_code(function_code, pdu)
        return pdu

    def read_exception_status(self, *, device_id: int = 1) -> ModbusPDU:
        """Read exception status (function code `0x07`).

        Args:
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response. Call the
                [bits][msl.equipment.interfaces.modbus.ModbusPDU.bits] method to get the
                ON/OFF state of each exception-status bit.
        """
        function_code = 0x07
        _ = self.write(function_code, device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], data=response[1:], count=8)
        self._check_function_code(function_code, pdu)
        return pdu

    def readwrite_registers(
        self,
        *,
        read_address: int = 0,
        read_count: int = 0,
        write_address: int = 0,
        address: int | None = None,
        values: int | Sequence[int] | NDArray[np.uint16] | None = None,
        device_id: int = 1,
    ) -> ModbusPDU:
        """Read/Write registers (function code `0x17`).

        Performs a combination of one read operation and one write operation in a single Modbus transaction.
        The write operation is performed before the read operation.

        Args:
            read_address: Starting holding-register address to read from. Must be in the range [0, 65535].
            read_count: The number of 16-bit registers to read. Must be in the range [1, 125].
            write_address: Starting holding-register address to write to. Must be in the range [0, 65535].
            address: Use as both the read and write address. Must be in the range [0, 65535].
            values: A sequence of values to write or a single value to write. The maximum sequence length is 121.
                Each value must be in the range [0, 65535]. See also
                [to_register_values][msl.equipment.interfaces.modbus.Modbus.to_register_values].
            device_id: Modbus device ID.

        Returns:
            The Modbus Protocol Data Unit of the response.
        """
        if read_count > 125:  # noqa: PLR2004
            msg = f"Requesting to read {read_count} holding registers, maximum allowed is 125"
            raise ValueError(msg)

        if values is None:
            values = []
        elif isinstance(values, int):
            values = [values]

        n = len(values)
        if n > 121:  # noqa: PLR2004
            msg = f"Too many values, {n}, to write to the Modbus registers, must be <= 121"
            raise ValueError(msg)

        if isinstance(values, np.ndarray):
            if values.dtype.str != ">u2":
                msg = f"numpy array must have a dtype of '>u2', got {values.dtype.str!r}"
                raise ValueError(msg)
            data = values.tobytes()
        elif n == 0:
            data = b""
        else:
            data = pack(f">{n}H", *values)

        if address is not None:
            read_address = address
            write_address = address

        function_code = 0x17
        _ = self.write(
            function_code,
            data=pack(">HHHHB", read_address, read_count, write_address, n, 2 * n) + data,
            device_id=device_id,
        )
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], data=response[2:], count=read_count)
        self._check_function_code(function_code, pdu)
        return pdu

    @staticmethod
    def to_register_values(
        data: float | Sequence[float] | NDArray[np.number], dtype: DTypeLike = np.uint16
    ) -> NDArray[np.uint16]:
        """Convert a value or a sequence of values to an unsigned, big-endian, 16-bit integer array.

        Args:
            data: The value(s) to convert. If a numpy array, the data type must be the same that the
                Modbus register address(es) require the value(s) to be in.
            dtype: The numpy data type to use to initially create a numpy array. This should be the
                same data type that the Modbus register address(es) require the value(s) to be in.
                Only used if `value` is not already a numpy array.

        Returns:
            An array that can be passed to [write_registers][msl.equipment.interfaces.modbus.Modbus.write_registers].
        """
        if isinstance(data, (float, int)):
            data = [data]

        dtype = data.dtype if isinstance(data, np.ndarray) else np.dtype(dtype)
        return np.asarray(data, dtype=dtype.newbyteorder(">")).view(">u2")

    def write(self, function_code: int, *, data: bytes | None = None, device_id: int = 1) -> int:
        """Write a Modbus message.

        Args:
            function_code: The Modbus function code.
            data: The data associated with the `function_code`.
            device_id: Modbus device ID.

        Returns:
            The number of bytes written.
        """
        return self._framer.write(device_id, function_code.to_bytes(1, "big") + (data or b""))

    def write_coil(self, address: int, value: bool, *, device_id: int = 1) -> ModbusPDU:  # noqa: FBT001
        """Write single coil (function code `0x05`).

        Args:
            address: Register address to write to. Must be in the range [0, 65535].
            value: Boolean to write. Sets the ON/OFF state of a single coil in the device.
            device_id: Modbus device ID.

        Returns:
            An echo of the request, after the register contents have been written.
        """
        function_code = 0x05
        _ = self.write(function_code, data=pack(">HH", address, 0xFF00 if value else 0x0000), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[1:])
        self._check_function_code(function_code, pdu)
        return pdu

    def write_coils(self, address: int, values: Sequence[bool] | NDArray[np.bool], *, device_id: int = 1) -> ModbusPDU:
        """Write multiple coils (function code `0x0F`).

        Args:
            address: Starting register address to write to. Must be in the range [0, 65535].
            values: A sequence of booleans to write. Sets the ON/OFF state of multiple coils
                in the device. The maximum sequence length is 1968.
            device_id: Modbus device ID.

        Returns:
            The response. The `data` attribute is composed of the starting register address
                and the number of registers that were written to.
        """
        n = len(values)
        if n > 0x07B0:  # noqa: PLR2004
            msg = f"Too many values, {n}, to write to the Modbus coils, must be <= {0x07B0}"
            raise ValueError(msg)

        data = np.packbits(np.asarray(values, dtype=bool), bitorder="little").tobytes()
        data = pack(">HHB", address, n, len(data)) + data

        function_code = 0x0F
        _ = self.write(function_code, data=data, device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[1:])
        self._check_function_code(function_code, pdu)
        return pdu

    def write_register(self, address: int, value: int, *, device_id: int = 1) -> ModbusPDU:
        """Write a single holding register value (function code `0x06`).

        Args:
            address: Register address to write to. Must be in the range [0, 65535].
            value: Value to write. Must be in the range [0, 65535].
            device_id: Modbus device ID.

        Returns:
            An echo of the request, after the register contents have been written.
        """
        function_code = 0x06
        _ = self.write(function_code, data=pack(">HH", address, value), device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[1:])
        self._check_function_code(function_code, pdu)
        return pdu

    def write_registers(
        self, address: int, values: Sequence[int] | NDArray[np.uint16], *, device_id: int = 1
    ) -> ModbusPDU:
        """Write to a block of contiguous registers (function code `0x10`).

        Args:
            address: Starting register address to write to. Must be in the range [0, 65535].
            values: A sequence of values to write. The maximum sequence length is 123.
                Each value must be in the range [0, 65535]. See also
                [to_register_values][msl.equipment.interfaces.modbus.Modbus.to_register_values].
            device_id: Modbus device ID.

        Returns:
            The response. The `data` attribute is composed of the starting register address
                and the number of registers that were written to.
        """
        n = len(values)
        if n > 123:  # noqa: PLR2004
            msg = f"Too many values, {n}, to write to the Modbus registers, must be <= 123"
            raise ValueError(msg)

        if isinstance(values, np.ndarray):
            if values.dtype.str != ">u2":
                msg = f"numpy array must have a dtype of '>u2', got {values.dtype.str!r}"
                raise ValueError(msg)
            data = pack(">HHB", address, n, 2 * n) + values.tobytes()
        else:
            data = pack(f">HHB{n}H", address, n, 2 * n, *values)

        function_code = 0x010
        _ = self.write(function_code, data=data, device_id=device_id)
        device_id, response = self.read()
        pdu = ModbusPDU(device_id, response[0], response[1:])
        self._check_function_code(function_code, pdu)
        return pdu

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for [read][msl.equipment.interfaces.modbus.Modbus.read]
        and [write][msl.equipment.interfaces.modbus.Modbus.write] operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """  # noqa: D205
        return self._framer.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._framer.timeout = value


class ModbusPDU:
    """Modbus Protocol Data Unit."""

    def __init__(self, device_id: int, function_code: int, data: bytes, count: int | None = None) -> None:
        """Modbus Protocol Data Unit."""
        self.count: int | None = count
        """[int][] &mdash; The number of registers/coils that were requested to read."""

        self.device_id: int = device_id
        """[int][] &mdash; Modbus device ID."""

        self.function_code: int = function_code
        """[int][] &mdash; Modbus function code."""

        self.data: bytes = data
        """[bytes][] &mdash; Modbus data."""

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return f"ModbusPDU(device_id={self.device_id}, function_code=0x{self.function_code:02X}, data={self.data!r})"

    def array(self, dtype: DTypeLike) -> NDArray[Any]:
        """[numpy.ndarray][] &mdash; Returns the register data as a [numpy.ndarray][] of the specified `dtype`."""
        if isinstance(dtype, type) or (isinstance(dtype, str) and dtype[0] not in "<>=|"):
            dtype = np.dtype(dtype).newbyteorder(">")  # force big endian
        return np.frombuffer(self.data, dtype=">u2").view(dtype)

    def bits(self, bitorder: Literal["big", "little"] = "little") -> NDArray[np.bool]:
        """[numpy.ndarray][] &mdash; Returns the states of the register bits that were requested."""
        data = np.frombuffer(self.data, dtype=np.uint8)
        return np.unpackbits(data, count=self.count, bitorder=bitorder).astype(bool)

    def decode(self, encoding: str = "utf-8") -> str:
        """[str][] &mdash; Returns the decoded response data using the `encoding` codec."""
        return self.data.decode(encoding)

    def float32(self, byteorder: Literal["big", "little"] = "big") -> float:
        """[float][] &mdash; Returns the register data as a 32-bit, floating-point number."""
        b = ">" if byteorder == "big" else "<"
        f32: float = unpack(b + "f", self.data)[0]
        return f32

    def float64(self, byteorder: Literal["big", "little"] = "big") -> float:
        """[float][] &mdash; Returns the register data as a 64-bit, floating-point number."""
        b = ">" if byteorder == "big" else "<"
        f64: float = unpack(b + "d", self.data)[0]
        return f64

    def int16(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as a signed, 16-bit integer."""
        b = ">" if byteorder == "big" else "<"
        i16: int = unpack(b + "h", self.data)[0]
        return i16

    def int32(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as a signed, 32-bit integer."""
        b = ">" if byteorder == "big" else "<"
        i32: int = unpack(b + "i", self.data)[0]
        return i32

    def int64(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as a signed, 64-bit integer."""
        b = ">" if byteorder == "big" else "<"
        i64: int = unpack(b + "q", self.data)[0]
        return i64

    def uint16(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as an unsigned, 16-bit integer."""
        b = ">" if byteorder == "big" else "<"
        u16: int = unpack(b + "H", self.data)[0]
        return u16

    def uint32(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as an unsigned, 32-bit integer."""
        b = ">" if byteorder == "big" else "<"
        u32: int = unpack(b + "I", self.data)[0]
        return u32

    def uint64(self, byteorder: Literal["big", "little"] = "big") -> int:
        """[int][] &mdash; Returns the register data as an unsigned, 64-bit integer."""
        b = ">" if byteorder == "big" else "<"
        u64: int = unpack(b + "Q", self.data)[0]
        return u64

    def unpack(self, format: str) -> tuple[Any, ...]:  # noqa: A002
        """[int][] &mdash; Return a tuple containing the register data unpacked according to the `format` string.

        Modbus data is in big-endian byte order, see [Byte Order, Size, and Alignment][byte-order-size-and-alignment]
        for more details.
        """
        return unpack(format, self.data)


# Exception codes 0x05 and 0x06 do not represent Modbus errors that should be raised, but treat them as such for now
EXCEPTIONS: dict[int, str] = {
    0x01: "Modbus function code is not supported",
    0x02: "Invalid Modbus register address requested",
    0x03: "The structure of the Modbus request message is invalid",
    0x04: "An unrecoverable error occurred while the Modbus device was attempting to perform the requested action",
    0x05: (
        "The Modbus device has accepted the request and is processing it, but it may take a long time to process "
        "(this is not an error but Get Comm Event Counter, function code 0x0B, has not been implemented yet)"
    ),
    0x06: "The Modbus device is busy processing a previous request",
    0x08: "Parity error in the memory of a Modbus device",
    0x0A: "The Modbus gateway is misconfigured or overloaded",
    0x0B: "The Modbus device is not present on the network",
}


class FramerType(Enum):
    """How to frame Modbus messages."""

    # REGEX must support every member name
    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"


class Framer:
    """Generic class to write/read a Modbus frame."""

    def __init__(self, interface: MessageBased) -> None:
        """Generic class to write/read a Modbus frame.

        Args:
            interface: The underlying MessageBased interface.
        """
        self.interface: MessageBased = interface

    def disconnect(self) -> None:
        """Disconnect from the underlying MessageBased interface."""
        self.interface.disconnect()

    def read(self) -> tuple[int, bytes]:
        """Read a framed Modbus message.

        Returns:
            The (device ID, Modbus Protocol Data Unit response).
        """
        raise NotImplementedError  # pragma: no cover

    def write(self, device_id: int, pdu: bytes) -> int:  # pyright: ignore[reportUnusedParameter]
        """Write a framed Modbus message.

        Args:
            device_id: Modbus device ID.
            pdu: Modbus Protocol Data Unit request.

        Returns:
            The number of bytes written.
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for read and write operations."""
        return self.interface.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self.interface.timeout = value


class SocketFramer(Framer):
    """Modbus framer for a socket."""

    def __init__(self, interface: MessageBased) -> None:
        """Modbus framer for a socket."""
        super().__init__(interface)
        self.transaction_id: int = 0

    def read(self) -> tuple[int, bytes]:  # pyright: ignore[reportImplicitOverride]
        """Read a framed Modbus message.

        Returns:
            The (device ID, Modbus Protocol Data Unit response).
        """
        header = self.interface.read(size=7, decode=False)
        tid, _, remaining, device_id = unpack(">HHHB", header)
        response = self.interface.read(size=remaining - 1, decode=False)  # read entire Frame, even if there is an error
        if tid != self.transaction_id:
            msg = f"Received unexpected Modbus transaction ID {tid}, expected {self.transaction_id}"
            raise MSLConnectionError(self.interface, msg)
        return device_id, response

    def write(self, device_id: int, pdu: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Write a framed Modbus message.

        Args:
            device_id: Modbus device ID.
            pdu: Modbus Protocol Data Unit request.

        Returns:
            The number of bytes written.
        """
        self.transaction_id += 1
        if self.transaction_id > 65535:  # noqa: PLR2004
            self.transaction_id = 1

        # Protocol ID = 0
        msg = pack(">HHHB", self.transaction_id, 0, len(pdu) + 1, device_id) + pdu
        return self.interface.write(msg)


class ParsedModbusAddress(NamedTuple):
    """The parsed result of a VISA-style address for the Modbus interface.

    Args:
        address: The VISA-style address to use for the Serial or Socket interface.
        framer: ASCII, RTU or SOCKET framer.
    """

    address: str
    framer: FramerType


def parse_modbus_address(address: str) -> ParsedModbusAddress | None:
    """Get the serial/socket address and the framer type.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the Modbus interface.
    """
    match = REGEX.match(address)
    if match is None:
        return None

    address = match["dev"] or match["com"]
    if not address:
        protocol = "UDP" if match["udp"] else "TCP"
        address = f"{protocol}::{match['host']}::{match['port'] or '502'}"

    if match["framer"]:
        framer = FramerType[match["framer"].upper()]  # REGEX forces a supported value
    elif address.startswith(("TCP", "UDP")):
        framer = FramerType.SOCKET
    else:
        framer = FramerType.RTU

    return ParsedModbusAddress(address=address, framer=framer)
