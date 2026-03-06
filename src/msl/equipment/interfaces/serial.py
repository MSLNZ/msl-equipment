"""Base class for equipment that is connected through a Serial port (or a USB-to-Serial adaptor)."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, NamedTuple

import serial

from msl.equipment.enumerations import DataBits, Parity, StopBits
from msl.equipment.utils import logger, to_enum

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from serial.tools.list_ports_common import ListPortInfo

    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"^(COM|ASRL|ASRLCOM)((?P<mock>/mock://)|(?P<find>\?::.*)|(?P<dev>/dev/[^\s:]+)|(?P<number>\d+))",
    flags=re.IGNORECASE,
)


class Serial(MessageBased, regex=REGEX):
    """Base class for equipment that is connected through a Serial port (or a USB-to-Serial adaptor)."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that is connected through a Serial port (or a USB-to-Serial adaptor).

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
            buffer_size (int): The maximum number of bytes to read at a time. _Default: `1024`_
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
            msg = f"Invalid Serial address {equipment.connection.address!r}"
            raise ValueError(msg)

        url = find_port(info.url[3:], equipment.connection.address) if info.url.startswith("?::") else info.url
        self._serial: serial.Serial = _init_serial(url, equipment.connection.properties)
        self._set_interface_timeout()

        self._buffer_size: int = equipment.connection.properties.get("buffer_size", 1024)
        self._buffer: bytearray = bytearray()

        try:
            self._serial.open()
        except serial.SerialException as e:
            raise MSLConnectionError(self, str(e)) from None

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]  # noqa: C901
        """Overrides method in MessageBased."""
        original_timeout = self._serial.timeout
        t0 = time.time()
        while True:
            if size is not None:
                if len(self._buffer) >= size:
                    msg = self._buffer[:size]
                    self._buffer = self._buffer[size:]
                    break

            elif self._read_termination:
                index = self._buffer.find(self._read_termination)
                if index != -1:
                    index += len(self._read_termination)
                    msg = self._buffer[:index]
                    self._buffer = self._buffer[index:]
                    break

            try:
                data = self._serial.read(max(1, min(self._buffer_size, self._serial.in_waiting)))
            except:
                self._serial.timeout = original_timeout
                raise
            else:
                self._buffer.extend(data)

            if len(self._buffer) > self._max_read_size:
                self._serial.timeout = original_timeout
                error = f"len(message) [{len(self._buffer)}] > max_read_size [{self._max_read_size}]"
                raise RuntimeError(error)

            if original_timeout is not None:
                # decrease the timeout when reading each packet so that the total
                # time to receive all packets preserves what was specified
                elapsed_time = time.time() - t0
                if elapsed_time > original_timeout:
                    self._serial.timeout = original_timeout
                    raise MSLTimeoutError(self)
                self._serial.timeout = max(0, original_timeout - elapsed_time)

        if original_timeout is not None:
            self._serial.timeout = original_timeout
        return bytes(msg)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        if hasattr(self, "_serial"):
            self._serial.timeout = self._timeout
            self._serial.write_timeout = self._timeout

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        return self._serial.write(message) or 0

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close the serial port."""
        if hasattr(self, "_serial") and self._serial.is_open:
            self._serial.close()
            super().disconnect()

    @property
    def serial(self) -> serial.Serial:
        """[pySerial.Serial][serial.Serial] &mdash; Returns the reference to the `pySerial` instance."""
        return self._serial


class ParsedSerialAddress(NamedTuple):
    """The parsed result of a VISA-style address for the Serial interface.

    Args:
        url: The port/url to pass to `serial.serial_for_url`.
    """

    url: str


def parse_serial_address(address: str) -> ParsedSerialAddress | None:
    """Get the url for the Serial port from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the Serial interface.
    """
    match = REGEX.match(address)
    if match is None:
        return None

    if match["mock"]:
        return ParsedSerialAddress(match["mock"][1:])

    if match["find"]:
        return ParsedSerialAddress(match["find"])

    if match["dev"]:
        return ParsedSerialAddress(match["dev"])

    return ParsedSerialAddress(f"COM{match['number']}")


class SerialPort(NamedTuple):
    """The VISA-style address, description and the full device name/path of a Serial port."""

    address: str
    description: str
    device: str


def find_ports(ports: list[ListPortInfo] | None = None) -> Iterator[SerialPort]:
    """Yields information about available Serial ports.

    Args:
        ports: Only used when running the tests to mock Serial ports.
    """
    if ports is None:
        from serial.tools.list_ports import comports  # noqa: PLC0415

        ports = sorted(comports())

    logger.debug("Searching for Serial ports")
    for port in ports:
        if port.hwid == "n/a":
            continue

        address = port.device if port.device.startswith("COM") else f"ASRL{port.device}"

        description = port.manufacturer or ""
        if port.product:
            description += f" {port.product}"
        if port.serial_number:
            description += f" {port.serial_number}"
        if not description:
            description = port.description
        description += f" {port.hwid}"

        yield SerialPort(address, description, port.device)


def find_port(search: str, address: str, ports: list[ListPortInfo] | None = None) -> str:
    """Find a particular Serial port.

    Args:
        search: The string to search for.
        address: The VISA-style address.
        ports: Only used when running the tests to mock Serial ports.

    Returns:
        The port url that can be passed to `_init_serial`.
    """
    if not search:
        msg = f"Must specify a search pattern for the Serial port, address={address!r}"
        raise ValueError(msg)

    descriptions: list[str] = []
    pattern = re.compile(search)
    for port in find_ports(ports):
        if pattern.search(port.description) is not None:
            logger.debug("Found matching Serial port %r", port.device)
            return port.device
        descriptions.append(port.description)

    options = "" if not descriptions else ", the following descriptions are available\n  " + "\n  ".join(descriptions)
    msg = f"Cannot find a Serial port for the address {address!r}{options}"
    raise ValueError(msg)


def _init_serial(url: str, p: dict[str, Any]) -> serial.Serial:
    """Create the unopened Serial instance.

    Args:
        url: The port/url to pass to `serial.serial_for_url`
        p: Connection properties.
    """
    return serial.serial_for_url(
        url=url,
        baudrate=p.get("baud_rate", p.get("baudrate", 9600)),
        bytesize=to_enum(p.get("data_bits", p.get("bytesize", DataBits.EIGHT)), DataBits, to_upper=True).value,
        parity=to_enum(p.get("parity", Parity.NONE), Parity, to_upper=True).value,
        stopbits=to_enum(p.get("stop_bits", p.get("stopbits", StopBits.ONE)), StopBits, to_upper=True).value,
        xonxoff=p.get("xon_xoff", p.get("xonxoff", False)),
        rtscts=p.get("rts_cts", p.get("rtscts", False)),
        dsrdtr=p.get("dsr_dtr", p.get("dsrdtr", False)),
        inter_byte_timeout=p.get("inter_byte_timeout"),
        do_not_open=True,
    )
