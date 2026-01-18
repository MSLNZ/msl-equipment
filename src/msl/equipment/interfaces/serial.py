"""Base class for equipment that is connected through a serial port (or a USB-to-Serial adaptor)."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, NamedTuple

import serial

from msl.equipment.enumerations import DataBits, Parity, StopBits
from msl.equipment.utils import to_enum

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from typing import Any

    from msl.equipment.schema import Equipment


REGEX = re.compile(r"^(COM|ASRL|ASRLCOM)((?P<dev>/dev/[^\s:]+)|(?P<number>\d+))", flags=re.IGNORECASE)


def _init_serial(port: str, p: dict[str, Any]) -> serial.Serial:
    """Create the unopened Serial instance.

    Args:
        port: Serial port name.
        p: Connection properties.
    """
    ser = serial.Serial()

    ser.baudrate = p.get("baud_rate", p.get("baudrate", 9600))

    size = p.get("data_bits", p.get("bytesize", DataBits.EIGHT))
    ser.bytesize = to_enum(size, DataBits, to_upper=True).value

    ser.dsrdtr = p.get("dsr_dtr", p.get("dsrdtr", False))

    ser.inter_byte_timeout = p.get("inter_byte_timeout")

    ser.parity = to_enum(p.get("parity", Parity.NONE), Parity, to_upper=True).value

    ser.port = port

    ser.rtscts = p.get("rts_cts", p.get("rtscts", False))

    bits = p.get("stop_bits", p.get("stopbits", StopBits.ONE))
    ser.stopbits = to_enum(bits, StopBits, to_upper=True).value

    ser.xonxoff = p.get("xon_xoff", p.get("xonxoff", False))

    return ser


class Serial(MessageBased, regex=REGEX):
    """Base class for equipment that is connected through a serial port (or a USB-to-Serial adaptor)."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that is connected through a serial port (or a USB-to-Serial adaptor).

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the serial communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased]. The
        [DataBits][msl.equipment.enumerations.DataBits], [Parity][msl.equipment.enumerations.Parity]
        and [StopBits][msl.equipment.enumerations.StopBits] enumeration names and values may also
        be used. For properties that specify an _alias_, you may also use the alternative name as
        the property name. See [serial.Serial][] for more details.

        Attributes: Connection Properties:
            baud_rate (int): The baud rate (_alias:_ baudrate). _Default: `9600`_
            data_bits (DataBits | str | int): The number of data bits: 5, 6, 7 or 8 (_alias:_ bytesize). _Default: `8`_
            dsr_dtr (bool): Whether to enable hardware (DSR/DTR) flow control (_alias:_ dsrdtr). _Default: `False`_
            inter_byte_timeout (float | None): The maximum duration, in seconds, that is allowed between two
                consecutive bytes in a read operation. A value of zero (or `None`) indicates that the inter-byte timeout
                condition is not used. On Windows, the minimum supported value is 0.001 seconds, on POSIX it is 0.1
                seconds. A value less than the minimum will disable the inter-byte timeout. _Default: `None`_
            parity (Parity | str): Parity checking: NONE, ODD, EVEN, MARK or SPACE. _Default: `NONE`_
            rts_cts (bool): Whether to enable hardware (RTS/CTS) flow control (_alias:_ rtscts). _Default: `False`_
            stop_bits (StopBits | str | float): The number of stop bits: 1, 1.5 or 2 (_alias:_ stopbits). _Default: `1`_
            xon_xoff (bool): Whether to enable software flow control (_alias:_ xonxoff). _Default: `False`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        info = parse_serial_address(equipment.connection.address)
        if info is None:
            msg = f"Invalid serial address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._serial: serial.Serial = _init_serial(info.port, equipment.connection.properties)
        self._set_interface_timeout()

        try:
            self._serial.open()
        except serial.SerialException as e:
            raise MSLConnectionError(self, str(e)) from None

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if size is not None:
            return self._serial.read(size)

        msg = bytearray()
        now = time.time
        read = self._serial.read
        r_term = self._read_termination
        timeout = self._timeout
        max_read_size = self._max_read_size
        t0 = now()
        while True:
            msg.extend(read(1))

            if r_term and msg.endswith(r_term):
                return bytes(msg)

            if len(msg) > max_read_size:
                error = f"len(message) [{len(msg)}] > max_read_size [{max_read_size}]"
                raise RuntimeError(error)

            if timeout and now() - t0 > timeout:
                raise MSLTimeoutError(self)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if hasattr(self, "_serial"):
            self._serial.timeout = self._timeout
            self._serial.write_timeout = self._timeout

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        n: int | None = self._serial.write(message)
        return n or 0

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the serial port."""
        if hasattr(self, "_serial") and self._serial.is_open:
            self._serial.close()
            super().disconnect()

    @property
    def serial(self) -> serial.Serial:
        """Returns the reference to the serial instance."""
        return self._serial


class ParsedSerialAddress(NamedTuple):
    """The parsed result of a VISA-style address for the serial interface.

    Args:
        port: Serial port name.
    """

    port: str


def parse_serial_address(address: str) -> ParsedSerialAddress | None:
    """Get the name of the serial port from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the serial interface.
    """
    match = REGEX.match(address)
    if match is None:
        return None

    if match["dev"]:
        return ParsedSerialAddress(match["dev"])

    return ParsedSerialAddress(f"COM{match['number']}")
