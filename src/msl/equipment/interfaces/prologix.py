"""Use [Prologix](https://prologix.biz/) hardware to establish a connection."""

from __future__ import annotations

import asyncio
import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

from msl.equipment.exceptions import MSLConnectionError
from msl.equipment.schema import Connection, Equipment, Interface
from msl.equipment.utils import ipv4_addresses, logger

from .serial import Serial
from .socket import Socket

if TYPE_CHECKING:
    from collections.abc import Awaitable, Sequence
    from typing import ClassVar, Literal

    from msl.equipment._types import MessageDataType, MessageFormat, NumpyArray1D, Sequence1D


# The value of `enet_port` should always be 1234 for the actual hardware, but make it configurable for the tests
REGEX = re.compile(
    r"Prologix::(?P<hw_address>[^\s:]+)(?P<enet_port>::\d{4,})?(::GPIB\d*)?::(?P<pad>\d+)(::(?P<sad>\d+))?",
    flags=re.IGNORECASE,
)

MIN_PAD_ADDRESS = 0
MAX_PAD_ADDRESS = 30
MIN_SAD_ADDRESS = 96
MAX_SAD_ADDRESS = 126
MIN_READ_TIMEOUT_MS = 1
MAX_READ_TIMEOUT_MS = 3000


class PrologixEthernet(Socket, append=False):
    """Prologix GPIB-ETHERNET Controller."""


class PrologixUSB(Serial, append=False):
    """Prologix GPIB-USB Controller."""


class Prologix(Interface, regex=REGEX):
    """Use [Prologix](https://prologix.biz/) hardware to establish a connection."""

    _controllers: ClassVar[dict[str, Serial | Socket]] = {}
    """A mapping of all Prologix Controllers that are being used to communicate with GPIB devices."""

    _selected_addresses: ClassVar[dict[str, str]] = {}
    """A mapping of the currently-selected GPIB address for all Prologix Controllers."""

    def __init__(self, equipment: Equipment) -> None:
        """Use [Prologix](https://prologix.biz/) hardware to establish a connection.

        For the GPIB-ETHERNET Controller, the format of the [address][msl.equipment.schema.Connection.address]
        string is `Prologix::HOST::1234::PAD[::SAD]`, where `HOST` is the hostname or IP address of the Prologix
        hardware, `1234` is the ethernet port that is open on the Prologix hardware, PAD (Primary GPIB Address)
        is an integer value between 0 and 30, and SAD (Secondary GPIB Address) is an integer value between
        96 and 126 (SAD is optional). For example,

        * `Prologix::192.168.1.110::1234::6`
        * `Prologix::192.168.1.110::1234::6::96`
        * `Prologix::prologix-00-21-69-01-31-04::1234::6` <br/>
           (typically, the hostname is `prologix-<MAC Address>`)

        For the GPIB-USB Controller, the format of the [address][msl.equipment.schema.Connection.address]
        string is `Prologix::PORT::PAD[::SAD]`, where `PORT` is the name of the serial port of the Prologix
        hardware, `PAD` (Primary GPIB Address) is an integer value between 0 and 30, and SAD (Secondary
        GPIB Address) is an integer value between 96 and 126 (SAD is optional). For example,

        * `Prologix::COM3::6`
        * `Prologix::/dev/ttyUSB0::6::112`

        Alternatively, to clearly separate the Prologix hardware address from the GPIB address you may include
        `GPIB::` in the address, for example,

        * `Prologix::192.168.1.110::1234::GPIB::6`
        * `Prologix::COM3::GPIB::22::96`

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for using Prologix hardware, as well as the _properties_ defined in,
        [Serial][msl.equipment.interfaces.serial.Serial] (for a GPIB-USB Controller) and in
        [Socket][msl.equipment.interfaces.socket.Socket] (for a GPIB-ETHERNET Controller).

        Attributes: Connection Properties:
            eoi (int): Whether to use the End or Identify line, either `0` (disable) or `1` (enable).
            eos (int): GPIB termination character(s): 0 (CR+LF), 1 (CR), 2 (LF) or 3 (no termination).
            eot_char (int): A user-specified character to append to network output when `eot_enable`
                is set to 1 and EOI is detected. Must be an ASCII value &lt;256, e.g., `eot_char=42`
                appends `*` (ASCII 42) when EOI is detected.
            eot_enable (int): Enables (1) or disables (0) the appending of a user-specified character, `eot_char`.
            mode (int): Configure the Prologix hardware to be a CONTROLLER (1) or DEVICE (0). _Default: `1`_
            read_tmo_ms (int): The inter-character timeout value, in milliseconds, to be used in the _read_
                command and the _spoll_ command, i.e., the delay since the last character was read. The
                `read_tmo_ms` timeout value is not to be confused with the total time for which data is
                read. The `read_tmo_ms` value must be between 1 and 3000 milliseconds.
        """
        self._addr: str = ""
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        info = parse_prologix_address(equipment.connection.address)
        if info is None:
            msg = f"Invalid Prologix address {equipment.connection.address!r}"
            raise ValueError(msg)

        pad = info.pad
        if pad < MIN_PAD_ADDRESS or pad > MAX_PAD_ADDRESS:
            msg = f"Invalid primary GPIB address {pad}, must be in the range [{MIN_PAD_ADDRESS}, {MAX_PAD_ADDRESS}]"
            raise ValueError(msg)

        sad = info.sad
        if sad is not None and (sad < MIN_SAD_ADDRESS or sad > MAX_SAD_ADDRESS):
            msg = f"Invalid secondary GPIB address {sad}, must be in the range [{MIN_SAD_ADDRESS}, {MAX_SAD_ADDRESS}]"
            raise ValueError(msg)

        self._addr = f"++addr {pad}" if sad is None else f"++addr {pad} {sad}"
        self._query_auto: bool = True
        self._hw_address: str = info.hw_address

        props = equipment.connection.properties

        try:
            self._controller: Serial | Socket = Prologix._controllers[self._hw_address]
        except KeyError:
            address = f"TCP::{self._hw_address}::{info.enet_port}" if info.enet_port else f"ASRL{self._hw_address}"
            e = Equipment(connection=Connection(address, **props))
            self._controller = PrologixEthernet(e) if info.enet_port else PrologixUSB(e)
            Prologix._controllers[self._hw_address] = self._controller
            Prologix._selected_addresses[self._hw_address] = ""

        # default is CONTROLLER mode
        mode = props.get("mode", 1)
        _ = self._controller.write(f"++mode {mode}")

        # set the options provided by the user
        for option in ["eoi", "eos", "eot_enable", "eot_char", "read_tmo_ms"]:
            value = props.get(option)
            if value is not None:
                _ = self._controller.write(f"++{option} {value}")

        self._ensure_gpib_address_selected()

    def _ensure_gpib_address_selected(self) -> None:
        # Make sure that the connection to the equipment for this instance of the Prologix class
        # is the equipment that the message will be sent to.
        if not self._addr:
            raise MSLConnectionError(self, "Disconnected from Prologix GPIB device")

        if self._addr != Prologix._selected_addresses[self._hw_address]:
            Prologix._selected_addresses[self._hw_address] = self._addr
            _ = self._controller.write(self._addr)

    @property
    def controller(self) -> Serial | Socket:
        """The connection to the Prologix Controller for this equipment.

        The returned type depends on whether a GPIB-USB or a GPIB-ETHERNET Controller is used to communicate
        with the equipment.
        """
        return self._controller

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the equipment.

        Calling this method does not close the underlying [Serial][msl.equipment.interfaces.serial.Serial]
        or [Socket][msl.equipment.interfaces.socket.Socket] connection to the Prologix Controller since
        the connection to the Prologix Controller may still be required to send messages to other GPIB
        devices that are attached to the Controller.
        """
        if self._addr:
            self._addr = ""
            super().disconnect()

    @property
    def encoding(self) -> str:
        """The encoding that is used for [read][msl.equipment.interfaces.prologix.Prologix.read]
        and [write][msl.equipment.interfaces.prologix.Prologix.write] operations.
        """  # noqa: D205
        return self._controller.encoding

    @encoding.setter
    def encoding(self, encoding: str) -> None:
        self._controller.encoding = encoding

    def group_execute_trigger(self, *addresses: int) -> int:
        """Send the Group Execute Trigger command to equipment at the specified addresses.

        Up to 15 addresses may be specified. If no address is specified then the
        Group Execute Trigger command is issued to the currently-addressed equipment.

        Args:
            addresses: The primary (and optional secondary) GPIB addresses. If a secondary address is
                specified then it must follow its corresponding primary address, for example,

                * group_execute_trigger(1, 11, 17) &#8594; primary, primary, primary
                * group_execute_trigger(3, 96, 12, 21) &#8594; primary, secondary, primary, primary

        Returns:
            The number of bytes written.
        """
        command = "++trg"
        if addresses:
            command += " " + " ".join(str(a) for a in addresses)
        return self._controller.write(command)

    @property
    def max_read_size(self) -> int:
        """The maximum number of bytes that can be [read][msl.equipment.interfaces.prologix.Prologix.read]."""
        return self._controller.max_read_size

    @max_read_size.setter
    def max_read_size(self, size: int) -> None:
        self._controller.max_read_size = size

    @overload
    def query(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> str: ...

    @overload
    def query(  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: Literal[False] = False,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> bytes: ...

    @overload
    def query(  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: bool = ...,
        dtype: MessageDataType = ...,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def query(  # noqa: PLR0913
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat | None = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        """Convenience method for performing a [write][msl.equipment.interfaces.prologix.Prologix.write]
        followed by a [read][msl.equipment.interfaces.prologix.Prologix.read].

        Args:
            message: The message to write to the equipment.
            delay: Time delay, in seconds, to wait between the _write_ and _read_ operations.
            decode: Whether to decode the returned message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the returned message. Can be any object
                that numpy [dtype][numpy.dtype] supports. See [from_bytes][msl.equipment.utils.from_bytes]
                for more details. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
            fmt: The format that the returned message data is in. Ignored if `dtype` is `None`.
                 See [from_bytes][msl.equipment.utils.from_bytes] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is
                returned as an [numpy.ndarray][], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """  # noqa: D205
        self._ensure_gpib_address_selected()

        if self._query_auto:
            _ = self._controller.write(b"++auto 1")

        reply = self._controller.query(message, delay=delay, decode=decode, dtype=dtype, fmt=fmt, size=size)  # type: ignore[misc, arg-type]

        if self._query_auto:
            _ = self._controller.write(b"++auto 0")

        return reply

    @property
    def query_auto(self) -> bool:
        """Whether to send `++auto 1` before and `++auto 0` after a
        [query][msl.equipment.interfaces.prologix.Prologix.query] to the Prologix Controller.
        """  # noqa: D205
        return self._query_auto

    @query_auto.setter
    def query_auto(self, enabled: bool) -> None:
        self._query_auto = bool(enabled)

    @overload
    def read(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        *,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> str: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: Literal[False] = False,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> bytes: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: bool = ...,
        dtype: MessageDataType = ...,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def read(
        self,
        *,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat | None = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        """Read a message from the equipment.

        See [MessageBased.read()][msl.equipment.interfaces.message_based.MessageBased.read] for more details.

        Args:
            decode: Whether to decode the message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the message. Can be any object
                that numpy [dtype][numpy.dtype] supports. See [from_bytes][msl.equipment.utils.from_bytes]
                for more details. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
            fmt: The format that the message data is in. Ignored if `dtype` is `None`.
                 See [from_bytes][msl.equipment.utils.from_bytes] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is returned
                as a numpy [ndarray][numpy.ndarray], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """
        self._ensure_gpib_address_selected()
        return self._controller.read(decode=decode, dtype=dtype, fmt=fmt, size=size)  # type: ignore[arg-type]

    @property
    def read_termination(self) -> bytes | None:
        """The termination character sequence that is used for a
        [read][msl.equipment.interfaces.prologix.Prologix.read] operation.

        Reading stops when the equipment stops sending data or the `read_termination`
        character sequence is detected. If you set the `read_termination` to be equal
        to a variable of type [str][], it will be encoded as [bytes][].
        """  # noqa: D205
        return self._controller.read_termination

    @read_termination.setter
    def read_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        self._controller.read_termination = termination

    @property
    def rstrip(self) -> bool:
        """Whether to remove trailing whitespace from [read][msl.equipment.interfaces.prologix.Prologix.read] messages."""  # noqa: E501
        return self._controller.rstrip

    @rstrip.setter
    def rstrip(self, value: bool) -> None:
        self._controller.rstrip = value

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, to use for the connection to the Prologix hardware.

        This timeout value is not to be confused with the `read_tmo_ms` command that Prologix Controllers
        accept. To set the inter-character delay, i.e., the delay since the last character was _read_ or
        for the _spoll_ command, [write][msl.equipment.interfaces.prologix.Prologix.write] the
        `++read_tmo_ms <time>` message to the Controller.
        """
        return self._controller.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._controller.timeout = value

    def write(
        self,
        message: bytes | str,
        *,
        data: Sequence1D | None = None,
        dtype: MessageDataType = "<f",
        fmt: MessageFormat | None = "ieee",
    ) -> int:
        """Write a message to the equipment.

        Args:
            message: The message to write to the equipment.
            data: The data to append to `message`. See [to_bytes][msl.equipment.utils.to_bytes]
                for more details.
            dtype: The data type to use to convert each element in `data` to bytes. Ignored
                if `data` is `None`. See [to_bytes][msl.equipment.utils.to_bytes] for more details.
            fmt: The format to use to convert `data` to bytes. Ignored if `data` is `None`.
                See [to_bytes][msl.equipment.utils.to_bytes] for more details.

        Returns:
            The number of bytes written.
        """
        self._ensure_gpib_address_selected()
        return self._controller.write(message, data=data, fmt=fmt, dtype=dtype)

    @property
    def write_termination(self) -> bytes | None:
        """The termination character sequence that is appended to
        [write][msl.equipment.interfaces.prologix.Prologix.write] messages.

        If you set the `write_termination` to be equal to a variable of type
        [str][], it will be encoded as [bytes][].
        """  # noqa: D205
        return self._controller.write_termination

    @write_termination.setter
    def write_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        self._controller.write_termination = termination


@dataclass
class ParsedPrologixAddress:
    """The parsed result of a VISA-style address for Prologix hardware.

    Args:
        enet_port: The port of the GPIB-ETHERNET Controller.
        hw_address: Hardware address. IP address or hostname for a Socket, port name for Serial.
        pad: The primary GPIB address.
        sad: The secondary GPIB address.
    """

    enet_port: int
    hw_address: str
    pad: int
    sad: int | None


def parse_prologix_address(address: str) -> ParsedPrologixAddress | None:
    """Parse the address to determine the connection hardware type and the GPIB address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for Prologix hardware.
    """
    match = REGEX.match(address)
    if match is None:
        return None

    return ParsedPrologixAddress(
        enet_port=0 if not match["enet_port"] else int(match["enet_port"][2:]),
        hw_address=match["hw_address"],
        pad=int(match["pad"]),
        sad=None if not match["sad"] else int(match["sad"]),
    )


@dataclass
class PrologixDevice:
    """A Prologix ENET-GPIB device on the network."""

    description: str
    addresses: list[str]


def find_prologix(  # noqa: C901, PLR0915
    *,
    ip: Sequence[str] | None = None,
    port: int = 1234,
    timeout: float = 1,
) -> dict[str, PrologixDevice]:
    """Find all Prologix ENET-GPIB Controllers that are on the network.

    To resolve the MAC address of a Prologix device, the `arp` program must be installed.
    On Linux, install `net-tools`. On Windows and macOS, `arp` should already be installed.

    Args:
        ip: The IP address(es) on the local computer to use to search for
            Prologix ENET-GPIB devices. If not specified, uses all network interfaces.
        port: The port number of the Prologix ENET-GPIB Controller.
        timeout: The maximum number of seconds to wait for a reply.

    Returns:
        The information about the Prologix ENET-GPIB devices that were found.
    """
    all_ips = ipv4_addresses() if not ip else set(ip)

    logger.debug("find Prologix ENET-GPIB devices: interfaces=%s, port=%s, timeout=%s", all_ips, port, timeout)

    if sys.platform == "win32":
        mac_regex = re.compile(r"([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})")
        arp_option = ["-a"]
    elif sys.platform == "darwin":
        # the 'arp' command on macOS prints the MAC address
        # using %x instead of %02x, so leading 0's are missing
        mac_regex = re.compile(r"([0-9a-fA-F]{1,2}(?::[0-9a-fA-F]{1,2}){5})")  # pyright: ignore[reportUnreachable]
        arp_option = ["-n"]
    else:
        mac_regex = re.compile(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})")  # pyright: ignore[reportUnreachable]
        arp_option = ["-n"]

    async def find_single(host: tuple[int, ...]) -> None:
        """Asynchronously find a single Prologix ENET-GPIB device."""
        host_str = "{}.{}.{}.{}".format(*host)
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host_str, port), timeout=timeout)
        except (OSError, asyncio.TimeoutError):
            return

        writer.write(b"++ver\n")
        await writer.drain()

        try:
            reply = await asyncio.wait_for(reader.readline(), timeout=timeout)
        except (OSError, asyncio.TimeoutError):
            return
        finally:
            writer.close()
            await writer.wait_closed()

        if not reply.startswith(b"Prologix"):
            return

        description = reply.decode().rstrip()

        # determine the MAC address
        shell = await asyncio.create_subprocess_shell(
            " ".join(["arp", *arp_option, host_str]), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await shell.communicate()
        if stderr:  # arp command not available?
            return

        addresses: set[str] = set()
        addresses.add(host_str)

        match = mac_regex.search(stdout.decode())
        if match is not None:
            mac = match[0]
            if sys.platform == "darwin":
                # the 'arp' command on macOS prints the MAC address
                # using %x instead of %02x, so leading 0's are missing
                bits = []  # pyright: ignore[reportUnreachable]
                for bit in mac.split(":"):
                    if len(bit) == 1:
                        bits.append("0" + bit)
                    else:
                        bits.append(bit)
                mac = "-".join(bits)

            mac = mac.replace(":", "-")
            description += f" (MAC Address: {mac})"
            addresses.add(f"prologix-{mac}")

        devices[host] = PrologixDevice(
            description=description,
            addresses=[f"Prologix::{a}::{port}::GPIB::<PAD>[::<SAD>]" for a in sorted(addresses)],
        )

    async def find_all() -> None:
        """Asynchronously find all Prologix ENET-GPIB devices."""
        tasks: list[Awaitable[None]] = []
        for item in all_ips:
            splitted = item.split(".")
            a, b, c = map(int, (item for item in splitted[:3]))
            tasks.extend([find_single((a, b, c, d)) for d in range(1, 255)])
        _ = await asyncio.gather(*tasks)

    devices: dict[tuple[int, ...], PrologixDevice] = {}
    asyncio.run(find_all())
    return {".".join(str(v) for v in k): devices[k] for k in sorted(devices)}
