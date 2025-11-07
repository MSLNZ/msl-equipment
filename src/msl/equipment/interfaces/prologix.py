"""Use [Prologix](https://prologix.biz/) hardware to establish a connection."""

from __future__ import annotations

import asyncio
import re
import sys
import time
from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING, overload

from msl.equipment.schema import Connection, Equipment, Interface
from msl.equipment.utils import ipv4_addresses, logger, to_bytes

from .message_based import MSLConnectionError
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


def _char_to_int(char: bytes | str | int) -> int:
    """Convert an char to an integer.

    Args:
        char: Must be an ASCII value in range [0..255].
    """
    if isinstance(char, (bytes, str)):
        char = ord(char)

    if char < 0 or char > 255:  # noqa: PLR2004
        msg = f"The <char> value must be in the range [0..255], got {char}"
        raise ValueError(msg)

    return char


class PrologixEthernet(Socket, append=False):
    """Prologix GPIB-ETHERNET Controller."""

    lock: Lock = Lock()


class PrologixUSB(Serial, append=False):
    """Prologix GPIB-USB Controller."""

    lock: Lock = Lock()


class Prologix(Interface, regex=REGEX):
    """Use [Prologix](https://prologix.biz/) hardware to establish a connection."""

    _controllers: ClassVar[dict[str, PrologixUSB | PrologixEthernet]] = {}
    """A mapping of all Prologix Controllers that are being used to communicate with GPIB devices."""

    _selected_addresses: ClassVar[dict[str, bytes]] = {}
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
        for using Prologix hardware, as well as the _properties_ defined in
        [Serial][msl.equipment.interfaces.serial.Serial] (for a GPIB-USB Controller) and in
        [Socket][msl.equipment.interfaces.socket.Socket] (for a GPIB-ETHERNET Controller).

        Attributes: Connection Properties:
            eoi (bool): Whether to assert the End or Identify (EOI) line. _Default: `True`_
            eos (int): GPIB termination character(s) to append to the message that is sent
                to the equipment. _Default: `3`_

                * `0`: CR+LF
                * `1`: CR
                * `2`: LF
                * `3`: no termination

            eot_char (int | str): A user-specified character to append to the reply that the Prologix hardware
                sends back to the computer when `eot_enable` is `True` and EOI is detected. Must be an ASCII
                value &lt;256, e.g., `eot_char=42` appends `*` (ASCII 42) when EOI is detected. _Default: `0`_
            eot_enable (bool): Enable or disable the appending of a user-specified character, `eot_char`,
                when the Prologix hardware sends a reply back to the computer. _Default: `False`_
            escape_characters (bool): Whether to escape the `LF`, `CR`, `ESC` and `+` characters when writing
                a message to the Prologix hardware. _Default: `True`_
            mode (int): Configure the Prologix hardware to be a CONTROLLER (`1`) or DEVICE (`0`). _Default: `1`_
            read_tmo_ms (int): The inter-character timeout value, in milliseconds, to be used in the *read*
                command and the *serial_poll* command, i.e., the delay since the last character was read. The
                `read_tmo_ms` timeout value is not to be confused with the total time for which data is
                read. The `read_tmo_ms` value must be between 1 and 3000 milliseconds and is only valid for
                CONTROLLER mode. _Default: `100`_

        !!! important
            The Prologix Connection Properties are the same for _all_ equipment that are attached to the
            Prologix hardware. If different equipment require different properties you must manage the
            settings appropriately, such as by writing `++eoi 0` to disable the use of the End or
            Identify line before reading from the equipment and then perhaps writing `++eoi 1`
            to re-enable it afterwards. Only the `escape_characters` property is associated with the
            [Prologix][] instance.
        """
        self._addr: bytes = b""
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

        self._addr = f"++addr {pad}\n".encode() if sad is None else f"++addr {pad} {sad}\n".encode()
        self._pad: int = pad
        self._sad: int | None = sad
        self._plus_plus_read_char: int | str = "eoi"
        self._hw_address: str = info.hw_address

        props = equipment.connection.properties

        try:
            self._controller: PrologixUSB | PrologixEthernet = Prologix._controllers[self._hw_address]
        except KeyError:
            address = f"TCP::{self._hw_address}::{info.enet_port}" if info.enet_port else f"ASRL{self._hw_address}"
            e = Equipment(connection=Connection(address, **props))
            self._controller = PrologixEthernet(e) if info.enet_port else PrologixUSB(e)
            Prologix._controllers[self._hw_address] = self._controller
            Prologix._selected_addresses[self._hw_address] = b""

        # There are two steps involved when writing a message to the equipment
        # 1) Computer -> Prologix
        # 2) Prologix -> Equipment
        # The Prologix needs to know when a message has been received in full, but cannot
        # consume any termination characters that are meant to be passed on to the Equipment.
        # If the same termination character is required by Prologix and the Equipment then there would be issues.
        # To avoid these potential issues Prologix passes a character on to the Equipment if a character is
        # preceded by the escape character, ESC (ASCII 27). All un-escaped LF, CR and ESC and + characters in
        # Step 1 are discarded by Prologix.

        # Set the controller backend to be un-escaped LF to signify that Prologix has received the full message
        self._write_termination: bytes | None = self._controller.write_termination  # termination for Equipment (Step 2)
        self._controller.write_termination = b"\n"  # termination for Prologix (Step 1)

        self._escape_characters: bool = bool(props.get("escape_characters", True))

        mode = int(props.get("mode", 1))
        _ = self._controller.write(f"++mode {mode}\n")

        eoi = 1 if props.get("eoi", True) else 0  # MODES AVAILABLE: CONTROLLER, DEVICE
        _ = self._controller.write(f"++eoi {eoi}\n")

        eos = props.get("eos", 3)  # MODES AVAILABLE: CONTROLLER, DEVICE
        _ = self._controller.write(f"++eos {eos}\n")

        self.set_eot_char(props.get("eot_char", 0))  # MODES AVAILABLE: CONTROLLER, DEVICE
        self.set_eot_enable(props.get("eot_enable", False))  # MODES AVAILABLE: CONTROLLER, DEVICE

        if mode == 1:  # MODES AVAILABLE: CONTROLLER
            read_tmo_ms = props.get("read_tmo_ms", 100)
            _ = self._controller.write(f"++read_tmo_ms {read_tmo_ms}\n")

        self._ensure_gpib_address_selected()

    def _ensure_gpib_address_selected(self) -> None:
        # Make sure that the connection to the equipment for this instance of the Prologix class
        # is the equipment that the message will be sent to.
        if not self._addr:
            raise MSLConnectionError(self, "Disconnected from Prologix GPIB device")

        if self._addr != Prologix._selected_addresses[self._hw_address]:
            Prologix._selected_addresses[self._hw_address] = self._addr
            _ = self._controller.write(self._addr)

    def _read(self, size: int | None) -> bytes:
        # Called in MultiMessageBased
        # Don't call self._controller.read because "++read eoi" must be sent
        return self.read(size=size, decode=False)

    def _set_interface_max_read_size(self) -> None:
        # Called in MultiMessageBased.__init__().
        # Here it's a no operation since self._controller gets the appropriate max_read_size when it is created.
        return

    def _set_interface_timeout(self) -> None:
        # Called in MultiMessageBased.__init__().
        # Here it's a no operation since self._controller gets the appropriate timeout when it is created.
        return

    def _write(self, message: bytes) -> int:
        # Called in MultiMessageBased
        # Don't call self._controller.write because the message must be checked for characters that must be escaped
        return self.write(message)

    def clear(self) -> None:
        """Send the Selected Device Clear (SDC) command."""
        with self._controller.lock:
            self._ensure_gpib_address_selected()
            _ = self._controller.write(b"++clr\n")

    @property
    def controller(self) -> Serial | Socket:
        """The connection to the Prologix Controller for this equipment.

        The returned type depends on whether a GPIB-USB or a GPIB-ETHERNET Controller is used to communicate
        with the equipment.

        Use this property if you want more direct access to the Prologix Controller.
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
            self._addr = b""
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

    @property
    def escape_characters(self) -> bool:
        r"""Whether to escape the `\n` (ASCII 10), `\r` (ASCII 13), `ESC` (ASCII 27) and `+` (ASCII 43)
        characters before a [write][msl.equipment.interfaces.prologix.Prologix.write] operation.
        """  # noqa: D205
        return self._escape_characters

    @escape_characters.setter
    def escape_characters(self, enable: bool) -> None:
        self._escape_characters = bool(enable)

    def group_execute_trigger(self, *addresses: int) -> None:
        """Send the Group Execute Trigger command to equipment at the specified addresses.

        Up to 15 addresses may be specified. If no address is specified then the
        Group Execute Trigger command is issued to the currently-addressed equipment.

        Args:
            addresses: The primary (and optional secondary) GPIB addresses. If a secondary address is
                specified then it must follow its corresponding primary address, for example,

                * `group_execute_trigger(1, 11, 17)` &#8594; primary, primary, primary
                * `group_execute_trigger(3, 96, 12, 21)` &#8594; primary, secondary, primary, primary
        """
        command = "++trg"
        if addresses:
            command += " " + " ".join(str(a) for a in addresses)
        _ = self._controller.write(command)

    def interface_clear(self) -> None:
        """Perform interface clear.

        Resets the GPIB bus by asserting the *interface clear* (IFC) bus line for a duration of at
        least 150 microseconds.
        """
        _ = self._controller.write(b"++ifc\n")

    def local(self) -> None:
        """Enables front panel operation of the device, `GTL` GPIB command."""
        with self._controller.lock:
            self._ensure_gpib_address_selected()
            _ = self._controller.write(b"++loc\n")

    @property
    def max_read_size(self) -> int:
        """The maximum number of bytes that can be [read][msl.equipment.interfaces.prologix.Prologix.read]."""
        return self._controller.max_read_size

    @max_read_size.setter
    def max_read_size(self, size: int) -> None:
        self._controller.max_read_size = size

    @property
    def pad(self) -> int:
        """Returns the primary GPIB address."""
        return self._pad

    def prologix_help(self) -> list[tuple[str, str]]:
        """Get the command-syntax help for the Prologix hardware.

        Returns:
            The help as a [list][] of `(command, description)` [tuple][]s.
        """
        h: list[tuple[str, str]] = []
        _ = self._controller.query(b"++help\n")  # ignore the first reply, "The following commands are available:"
        while True:
            cmd, msg = map(str.strip, self._controller.read().split("--"))
            h.append((cmd, msg))
            if cmd == "++help":  # pragma: no branch
                return h

    @overload
    def query(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat = ...,
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
        fmt: MessageFormat = ...,
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
        fmt: MessageFormat = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def query(
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        """Convenience method for performing a [write][msl.equipment.interfaces.prologix.Prologix.write]
        followed by a [read][msl.equipment.interfaces.prologix.Prologix.read].

        Args:
            message: The message to write to the equipment.
            delay: Time delay, in seconds, to wait between the _write_ and _read_ operations.
            decode: Whether to decode the returned message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the returned message. Can be any object that numpy
                [dtype][numpy.dtype] supports. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
                See [MessageDataType][msl.equipment._types.MessageDataType] for more details.
            fmt: The format that the returned message data is in. Ignored if `dtype` is `None`.
                See [MessageFormat][msl.equipment._types.MessageFormat] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is
                returned as an [numpy.ndarray][], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """  # noqa: D205
        if not isinstance(message, bytes):
            message = message.encode(encoding=self._controller.encoding)

        if message.startswith(b"++"):  # message is (probably) for the Prologix hardware
            if not message.endswith(b"\n"):
                message += b"\n"
            with self._controller.lock:
                self._ensure_gpib_address_selected()
                return self._controller.query(message, delay=delay, decode=decode, dtype=dtype, fmt=fmt, size=size)

        _ = self.write(message)
        if delay > 0:
            time.sleep(delay)
        if dtype:
            return self.read(dtype=dtype, fmt=fmt, size=size)
        return self.read(decode=decode, size=size)

    @overload
    def read(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        *,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat = ...,
        size: int | None = ...,
    ) -> str: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: Literal[False] = False,
        dtype: None = None,
        fmt: MessageFormat = ...,
        size: int | None = ...,
    ) -> bytes: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: bool = ...,
        dtype: MessageDataType = ...,
        fmt: MessageFormat = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def read(
        self,
        *,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        r"""Read a message from the equipment.

        See [MessageBased.read()][msl.equipment.interfaces.message_based.MessageBased.read] for more
        details about when this method returns.

        !!! note "See Also"
            [set_plus_plus_read_char][msl.equipment.interfaces.prologix.Prologix.set_plus_plus_read_char]

        Args:
            decode: Whether to decode the message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the returned message. Can be any object that numpy
                [dtype][numpy.dtype] supports. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
                See [MessageDataType][msl.equipment._types.MessageDataType] for more details.
            fmt: The format that the returned message data is in. Ignored if `dtype` is `None`.
                See [MessageFormat][msl.equipment._types.MessageFormat] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is returned
                as a numpy [ndarray][numpy.ndarray], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """
        with self._controller.lock:
            self._ensure_gpib_address_selected()
            _ = self._controller.write(f"++read {self._plus_plus_read_char}\n")
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

    def remote_enable(self, state: bool) -> None:  # noqa: FBT001
        """Whether to enable or disable front panel operation of the device.

        Args:
            state: If `True`, the device goes to remote mode (local lockout), `False` for local mode.
        """
        if state:
            with self._controller.lock:
                self._ensure_gpib_address_selected()
                _ = self._controller.write(b"++llo\n")
        else:
            self.local()

    def reset_controller(self) -> None:
        """Performs a power-on reset of the Prologix Controller.

        It takes about five seconds for the Controller to reboot.
        """
        _ = self._controller.write(b"++rst\n")

    @property
    def rstrip(self) -> bool:
        """Whether to remove trailing whitespace from [read][msl.equipment.interfaces.prologix.Prologix.read] messages."""  # noqa: E501
        return self._controller.rstrip

    @rstrip.setter
    def rstrip(self, value: bool) -> None:
        self._controller.rstrip = value

    @property
    def sad(self) -> int | None:
        """Returns the secondary GPIB address."""
        return self._sad

    def serial_poll(self, pad: int | None = None, sad: int | None = None) -> int:
        """Read status byte / serial poll.

        Args:
            pad: The primary GPIB address to poll. If not specified, uses the
                primary address of the instantiated class.
            sad: The secondary GPIB address to poll. If not specified, uses the
                secondary address of the instantiated class.

        Returns:
            The [status value](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html).
        """
        p = self._pad if pad is None else pad
        s = self._sad if sad is None else sad
        cmd = f"++spoll {p} {s}" if s is not None else f"++spoll {p}"
        try:
            return int(self._controller.query(cmd, decode=False))
        except ValueError:  # pragma: no cover
            return 0

    def set_eot_char(self, char: bytes | str | int) -> None:
        """Set a user-specified character to append to the reply from the Prologix Controller back to the computer.

        This character is appended only if `eot_enable` is `True` and EOI is detected.

        !!! note "See Also"
            [set_eot_enable][msl.equipment.interfaces.prologix.Prologix.set_eot_enable]

        Args:
            char: Must be an ASCII value &lt;256, e.g., `42` appends `*` (ASCII 42) when EOI is detected.
        """
        _ = self._controller.write(f"++eot_char {_char_to_int(char)}\n")

    def set_eot_enable(self, enable: bool | int) -> None:  # noqa: FBT001
        """Enables or disables the appending of a user-specified character.

        !!! note "See Also"
            [set_eot_char][msl.equipment.interfaces.prologix.Prologix.set_eot_char]

        Args:
            enable: Whether to enable or disable the appending of a user-specified character.
        """
        state = 1 if enable else 0
        _ = self._controller.write(f"++eot_enable {state}\n")

    def set_plus_plus_read_char(self, char: bytes | str | int | None = None) -> None:
        """Set the character to send when the `++read eoi|<char>` message is written in [read][msl.equipment.interfaces.prologix.Prologix.read].

        Args:
            char: If `None` then the `++read eoi` message is sent, otherwise `++read <char>`.
                The decimal value of `char` must be in the range [0..255].
        """  # noqa: E501
        self._plus_plus_read_char = "eoi" if char is None else _char_to_int(char)

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, to use for the connection to the Prologix hardware.

        This timeout value is not to be confused with the `read_tmo_ms` command that Prologix Controllers
        accept. To set the inter-character delay, i.e., the delay since the last character was *read* or
        for the *serial_poll* command, [write][msl.equipment.interfaces.prologix.Prologix.write] the
        `++read_tmo_ms <time>` message to the Controller (or define it in the
        [Connection][msl.equipment.schema.Connection] *properties*).
        """
        return self._controller.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._controller.timeout = value

    def trigger(self) -> None:
        """Trigger device."""
        cmd = f"++trg {self._pad}\n" if self._sad is None else f"++trg {self._pad} {self._sad}\n"
        _ = self._controller.write(cmd)

    def wait(
        self,
        mask: int,
        *,
        delay: float = 0.05,
        pad: int | None = None,
        sad: int | None = None,
        timeout: float | None = None,
    ) -> int:
        """Wait for an event.

        Args:
            mask: Wait until one of the conditions specified in `mask` is true.
                See [here](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html)
                for the bit values that the `mask` supports. If `mask=0`,
                then this method will return immediately.
            delay: The number of seconds to wait between checking for an event.
            pad: The primary GPIB address to poll. If not specified, uses the
                primary address of the instantiated class.
            sad: The secondary GPIB address to poll. If not specified, uses the
                secondary address of the instantiated class.
            timeout: The maximum number of seconds to wait before raising [TimeoutError][]
                if an event has not occurred. A value of `None` means wait forever.

        Returns:
            The [status value](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html).
        """
        p = self._pad if pad is None else pad
        s = self._sad if sad is None else sad
        t0 = time.time()
        while True:
            status = self.serial_poll(pad=p, sad=s)
            if (status & mask) or (mask == 0):
                return status

            if timeout and time.time() > t0 + timeout:
                msg = f"An event has not occurred after {timeout} seconds"
                raise TimeoutError(msg)

            time.sleep(delay)

    def wait_for_srq(self, *, delay: float = 0.05, timeout: float | None = None) -> int:
        """Wait for the SRQ interrupt line to be asserted.

        This method will return when the Prologix Controller receives a service request
        from *any* device. If there are multiple devices connected to the Prologix Controller,
        you must determine which device asserted the service request.

        Args:
            delay: The number of seconds to wait between checking if SRQ has been asserted.
            timeout: The maximum number of seconds to wait before raising [TimeoutError][]
                if the SRQ line is not asserted. A value of `None` means wait forever.

        Returns:
            The [status value](https://linux-gpib.sourceforge.io/doc_html/reference-globals-ibsta.html).
        """
        t0 = time.time()
        while True:
            if int(self._controller.query(b"++srq\n")) == 1:
                return self.serial_poll()

            if timeout and time.time() > t0 + timeout:
                msg = f"SRQ line has not been asserted after {timeout} seconds"
                raise TimeoutError(msg)

            time.sleep(delay)

    def write(
        self,
        message: bytes | str,
        *,
        data: Sequence1D | None = None,
        dtype: MessageDataType = "<f",
        fmt: MessageFormat = "ieee",
    ) -> int:
        """Write a message to the equipment.

        !!! note "See Also"
            [escape_characters][msl.equipment.interfaces.prologix.Prologix.escape_characters]

        Args:
            message: The message to write to the equipment.
            data: The data to append to `message`.
            dtype: The data type to use to convert each element in `data` to bytes. Ignored
                if `data` is `None`. See [MessageDataType][msl.equipment._types.MessageDataType]
                for more details.
            fmt: The format to use to convert `data` to bytes. Ignored if `data` is `None`.
                See [MessageFormat][msl.equipment._types.MessageFormat] for more details.

        Returns:
            The number of bytes written.
        """
        if not isinstance(message, bytes):
            message = message.encode(encoding=self._controller.encoding)

        if message.startswith(b"++"):
            # The message is (probably) for the Prologix hardware
            # Prologix termination is b"\n" not self._write_termination (which is for the Equipment)
            if not message.endswith(b"\n"):
                message += b"\n"
            return self._controller.write(message, data=data, dtype=dtype, fmt=fmt)

        if data is not None:
            message += to_bytes(data, fmt=fmt, dtype=dtype)

        if self._write_termination and not message.endswith(self._write_termination):
            message += self._write_termination

        if self._escape_characters:
            # Escape \n \r ESC + characters so that Prologix does not consume them but passes them on to the Equipment
            # ASCII code ESC is decimal 27 (octal 033, hexadecimal 0x1B)
            message = message.replace(b"\033", b"\033\033")  # must be first
            message = message.replace(b"\n", b"\033\n")
            message = message.replace(b"\r", b"\033\r")
            message = message.replace(b"+", b"\033+")

        with self._controller.lock:
            self._ensure_gpib_address_selected()
            # Add an un-escaped \n for Prologix to know it has received the full message from the Computer
            return self._controller.write(message + b"\n")

    @property
    def write_termination(self) -> bytes | None:
        """The termination character sequence that is appended to
        [write][msl.equipment.interfaces.prologix.Prologix.write] messages.

        If you set the `write_termination` to be equal to a variable of type
        [str][], it will be encoded as [bytes][].
        """  # noqa: D205
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        # termination character sequence sent from Prologix to the Equipment (Step 2)
        if termination is None or isinstance(termination, bytes):
            self._write_termination = termination
        else:
            self._write_termination = termination.encode(self._controller.encoding)


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
    logger.debug("Broadcasting for Prologix ENET-GPIB Controllers: %s", all_ips)

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
