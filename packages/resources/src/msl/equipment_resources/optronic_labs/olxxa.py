"""Communicate with a DC current source from [Optronic Laboratories](https://optroniclabs.com/){:target="_blank"}.

Compatible models are OL 16A, 65A and 83A.
"""

from __future__ import annotations

import re
import struct
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

from msl.equipment_resources.multi_message_based import MultiMessageBased

from msl.equipment.interfaces import GPIB, MSLConnectionError
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment


@dataclass
class LampInfo:
    """Information about the currently-selected lamp.

    Args:
        number: The lamp number (between 0 and 9, inclusive).
        value: The target value.
        unit: The unit of `value`.
    """

    number: int
    value: float
    unit: str


EOT = 0xFF
ACK = 0x06
NAK = 0x15
STX = 0x02
ETX = 0x03

MAX_LAMPS = 9


class OLxxA(MultiMessageBased, manufacturer=r"Optronic", model=r"(OL)?\s*(16|65|83)A", flags=re.IGNORECASE):
    """Communicate with a DC current source from [Optronic Laboratories](https://optroniclabs.com/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a DC current source from Optronic Laboratories.

        !!! warning
            The connection interface must be selected (using the buttons on the
            front panel) to be either RS-232 or IEEE-488 after the Current Source
            is initially powered on. Even if this is the default power-on interface,
            it must be manually re-selected before communication will work.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for an Optronic Current Source, as well as the _properties_ for
        [Serial][msl.equipment.interfaces.serial.Serial] if using RS-232 as the interface
        or [GPIB][msl.equipment.interfaces.gpib.GPIB] if using IEEE-488 as the interface.

        Attributes: Connection Properties:
            address (int): Internal address of the device (RS-232 only). _Default: `1`_
            delay (float): Number of seconds to wait between a write-read transaction (RS-232 only). _Default: `0.1`_
            use_ack_nak (bool): Whether to force ACK/NAK for checksum verification. The default value
                depends on the type of interface that is used. It is `True` if the interface is
                detected as serial and `False` otherwise.
        """
        super().__init__(equipment)

        self._system_status_byte: int = 0
        self._options: tuple[int, ...] = (40, 50, 60, 70, 80, 90, 95)
        self._str_options: tuple[int, ...] = (60, 90, 95)

        assert equipment.connection is not None  # noqa: S101
        p = equipment.connection.properties
        self._address: int = int(p.get("address", 1))
        self._delay: float = float(p.get("delay", 0.1))
        self._use_ack_nak: bool = p.get("use_ack_nak", hasattr(self._interface, "serial"))

        if self._use_ack_nak:
            self.read_termination = struct.pack("B", ETX)  # pyright: ignore[reportUnannotatedClassAttribute]
            self.write_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]

    @staticmethod
    def _check_lamp_number(lamp: int) -> None:
        if lamp < 0 or lamp > MAX_LAMPS:
            msg = f"Invalid lamp number {lamp}, must be in the range [0, 9]"
            raise ValueError(msg)

    @staticmethod
    def _checksum(buffer: bytes) -> bytes:
        """Convert bytes to a checksum."""
        s = sum(struct.unpack(f"{len(buffer)}B", buffer))
        return struct.pack("B", s & 0x7F)

    def _receive(self, expected: bytes, iteration: int = 0) -> list[bytes]:
        """Receive a message."""
        if not self._use_ack_nak:
            if isinstance(self._interface, GPIB):
                return _receive_gpib(self, self._interface, expected=expected, iteration=iteration)

            msg = "Only GPIB interface is currently supported"
            raise MSLConnectionError(self, msg)

        time.sleep(self._delay)

        # initiate
        cmd = struct.pack("BB", EOT, self._address | 0x80)
        reply = self.query(cmd, size=1, decode=False)
        r = struct.unpack("B", reply)[0]
        if r != ACK:
            msg = "The power supply does not have data to send"
            if iteration < 3:  # noqa: PLR2004
                logger.debug("%s, read again", msg)
                return self._receive(expected, iteration=iteration + 1)
            raise MSLConnectionError(self, msg)

        # read until the ETX character
        reply = self.read(decode=False)

        # read the checksum
        chk = self.read(size=1, decode=False)

        # send the ACK/NAK reply based on whether the checksums match
        if self._checksum(reply) == chk:
            _ = self.write(struct.pack("B", ACK))
        else:
            _ = self.write(struct.pack("B", NAK))
            msg = "The checksum is invalid"
            raise MSLConnectionError(self, msg)

        values = reply[1:-1].split()

        # all replies start with the command character that was sent,
        # sometimes the reply is from a previous request so read again
        if values[0] != expected:
            msg = f"Invalid reply character, {bytes(values[0])!r} != {expected!r}"
            if iteration < 3:  # noqa: PLR2004
                logger.debug("%s, read again", msg)
                return self._receive(expected, iteration=iteration + 1)
            raise MSLConnectionError(self, msg)

        # update the cached system status byte for this command
        self._system_status_byte = int(bytes(values[-1]), 16)

        return values[1:-1]

    def _send(self, message: bytes) -> None:
        """Send a message."""
        if not self._use_ack_nak:
            packed = struct.pack(f"B{len(message)}sB", STX, message, ETX)
            _ = self.write(packed)
            return

        # initiate
        init = struct.pack("BB", EOT, self._address)
        reply = self.query(init, size=1, decode=False)
        r = struct.unpack("B", reply)[0]
        if r != ACK:
            msg = "The power supply cannot receive data"
            raise MSLConnectionError(self, msg)

        # send request
        buffer = struct.pack(f"B{len(message)}sB", STX, message, ETX)
        buffer += self._checksum(buffer)
        reply = self.query(buffer, size=1, decode=False)
        r = struct.unpack("B", reply)[0]
        if r != ACK:
            msg = "The checksum is invalid"
            raise MSLConnectionError(self, msg)

    def get_current(self) -> float:
        """Get the output current."""
        self._send(b"c")
        reply = self._receive(b"c")
        return float(reply[0])

    @overload
    def get_option(self, lamp: int, option: Literal[40, 50, 70, 80]) -> float: ...

    @overload
    def get_option(self, lamp: int, option: Literal[60, 90, 95]) -> str: ...

    def get_option(self, lamp: int, option: Literal[40, 50, 60, 70, 80, 90, 95]) -> str | float:
        """Get the value of a lamp configuration option.

        Args:
            lamp: The lamp number (between 0 and 9, inclusive).
            option: The option type to read. Must be one of the following values

                * `40`: Lamp Hours
                * `50`: Recalibration interval (hours)
                * `60`: Target units &#8594; `"A"`, `"V"` or `"W"`
                * `70`: Target value
                * `80`: Current limit
                * `90`: Lamp description text
                * `95`: Wattage &#8594; `"L"` or `"H"`

        Returns:
            The value of the `option` that was requested. The return type depends on the `option` value.
        """
        self._check_lamp_number(lamp)

        if option not in self._options:
            msg = f"Invalid option value {option}"
            raise ValueError(msg)

        msg = f"Y {lamp:.0f} {option:.0f}"
        self._send(msg.encode("ascii"))
        reply = self._receive(b"Y")

        if len(reply) == 3:  # noqa: PLR2004
            num, dt, dv = reply
        else:
            num, dt = reply[:2]
            dv = b"".join(reply[2:])

        n = int(num)
        if n != lamp:
            msg = f"Lamp number mismatch, {n} != {lamp}"
            raise MSLConnectionError(self, msg)

        t = int(dt)
        if t != option:
            msg = f"Data type mismatch, {t} != {option}"
            raise MSLConnectionError(self, msg)

        if t in self._str_options:
            return dv.decode("ascii").strip("|")
        return float(dv)

    def get_voltage(self) -> float:
        """Get the output voltage."""
        self._send(b"v")
        reply = self._receive(b"v")
        return float(reply[0])

    def get_wattage(self) -> float:
        """Get the output wattage."""
        self._send(b"w")
        reply = self._receive(b"w")
        return float(reply[0])

    def reset(self) -> None:
        """Reset the communication buffers."""
        self._send(b"Z")
        _ = self._receive(b"Z")

    def select_lamp(self, lamp: int) -> None:
        """Select a lamp.

        Args:
            lamp: The lamp number (between 0 and 9, inclusive).
        """
        self._check_lamp_number(lamp)
        msg = f"S {lamp:.0f}".encode("ascii")

        # selecting a lamp is buggy, so try to do it twice
        try:
            self._send(msg)
            _ = self._receive(b"S")
        except MSLConnectionError:
            self._send(msg)
            _ = self._receive(b"S")

    def set_current(self, amps: float) -> float:
        """Set the target output current.

        Args:
            amps: The target current, in Amps. If the value is above the target current limit for
                the presently selected lamp setup or if the value is less than the minimum
                supported current, the target current will not change.

        Returns:
            The actual value of the output current after it was set.
        """
        msg = f"C {amps:.5f}"
        self._send(msg.encode("ascii"))
        reply = self._receive(b"C")
        return float(reply[0])

    def set_option(self, lamp: int, option: int, value: str | float) -> None:
        """Set a value for one of the lamp configuration options.

        Args:
            lamp: The lamp number (between 0 and 9, inclusive).
            option: The option type to update. Must be one of the following values.

                * `40`: Lamp Hours
                * `50`: Recalibration interval (hours)
                * `60`: Target units, `value` must be `"A"`, `"V"` or `"W"`
                * `70`: Target value
                * `80`: Current limit
                * `90`: Lamp description text
                * `95`: Wattage, `value` must be `"L"` or `"H"`

            value: The value to write for `option`.
        """
        self._check_lamp_number(lamp)
        if option not in self._options:
            msg = f"Invalid option value {option}"
            raise ValueError(msg)

        msg = f"X {lamp:.0f} {option:.0f} {value}"
        self._send(msg.encode("ascii"))
        _ = self._receive(b"X")

    def set_voltage(self, volts: float) -> float:
        """Set the target output voltage.

        Args:
            volts: The target voltage, in Volts. If the value is above the
                target voltage limit for the presently selected lamp setup or if
                the value is less than the minimum supported voltage, the target
                voltage will not change.

        Returns:
            The actual value of the output voltage after it was set.
        """
        msg = f"V {volts:.5f}"
        self._send(msg.encode("ascii"))
        reply = self._receive(b"V")
        return float(reply[0])

    def set_wattage(self, watts: float) -> float:
        """Set the target output wattage.

        Args:
            watts: The target wattage, in Watts. If the value is above the
                target wattage limit for the presently selected lamp setup or if
                the value is less than the minimum supported wattage, the target
                wattage will not change.

        Returns:
            The actual value of the output wattage after it was set.
        """
        msg = f"W {watts:.5f}"
        self._send(msg.encode("ascii"))
        reply = self._receive(b"W")
        return float(reply[0])

    def state(self) -> bool:
        """Returns whether the output is on or off."""
        self._send(b"b")
        reply = self._receive(b"b")
        return reply[0] == b"1"

    @property
    def system_status_byte(self) -> int:
        """The system status byte that is returned in every reply.

        It is constructed as follows:

        * bit 7: Busy flag (the device is performing a function)
        * bit 6: Reserved
        * bit 5: Reserved
        * bit 4: Lamp status (0=off, 1=on)
        * bit 3: Reserved
        * bit 2: Reserved
        * bit 1: Seeking current (1=current is ramping)
        * bit 0: Reserved

        """
        return self._system_status_byte

    def target_info(self) -> LampInfo:
        """Get the target information of the currently-selected lamp.

        Returns:
            The target information.
        """
        self._send(b"t")
        number, value, unit = self._receive(b"t")
        return LampInfo(number=int(number), value=float(value), unit=unit.decode("ascii"))

    def turn_off(self) -> None:
        """Turn the output off."""
        self._send(b"B 0")
        _ = self._receive(b"B")

    def turn_on(self) -> None:
        """Turn the output on."""
        self._send(b"B 1")
        _ = self._receive(b"B")

    def zero_voltage_monitor(self) -> None:
        """Zero the voltage monitor."""
        self._send(b"D")
        _ = self._receive(b"D")


def _receive_gpib(cls: OLxxA, interface: GPIB, expected: bytes, iteration: int = 0) -> list[bytes]:
    while True:
        _ = interface.wait_for_srq()
        if interface.serial_poll() & 0b00000001:  # Bit 0: active high means Message AVailable:
            break

    reply = interface.read(decode=False).rstrip()
    values = reply[1:-1].split()

    # all replies start with the command character that was sent, sometimes
    # (for the RS-232 interface) the reply is from a previous request so
    # read again ... did not observe this with GPIB, but keep it
    if values[0] != expected:
        msg = f"Invalid reply character, {bytes(values[0])!r} != {expected!r}"
        if iteration < 3:  # noqa: PLR2004
            logger.debug("%s, read again", msg)
            return _receive_gpib(cls, interface, expected, iteration=iteration + 1)
        raise MSLConnectionError(cls, msg)

    # update the cached system status byte for this command
    cls._system_status_byte = int(bytes(values[-1]), 16)  # pyright: ignore[reportPrivateUsage]

    return values[1:-1]
