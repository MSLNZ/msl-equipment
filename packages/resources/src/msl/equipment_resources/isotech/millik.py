"""[IsoTech](https://isotech.co.uk/) milliK Precision Thermometer.

There can also be multiple millisKanner Channel Expanders connected to the milliK.
"""

# cSpell: ignore SPRT
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, overload

from msl.equipment_resources.multi_message_based import MultiMessageBased

from msl.equipment.interfaces import MSLConnectionError
from msl.equipment.utils import to_enum

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Literal

    from msl.equipment.interfaces import MessageBased
    from msl.equipment.schema import Equipment


class Type(Enum):
    """Standard thermocouple types.

    Attributes:
        B (str): `"TYPE B"`
        E (str): `"TYPE E"`
        J (str): `"TYPE J"`
        K (str): `"TYPE K"`
        L (str): `"TYPE L"`
        N (str): `"TYPE N"`
        R (str): `"TYPE R"`
        S (str): `"TYPE S"`
        T (str): `"TYPE T"`
        AU_PT (str): `"TYPE AU-PT"`
        PT_PD (str): `"TYPE PT-PD"`
    """

    B = "TYPE B"
    E = "TYPE E"
    J = "TYPE J"
    K = "TYPE K"
    L = "TYPE L"
    N = "TYPE N"
    R = "TYPE R"
    S = "TYPE S"
    T = "TYPE T"
    AU_PT = "TYPE AU-PT"
    PT_PD = "TYPE PT-PD"


@dataclass
class Resistance:
    """A channel configured to measure resistance.

    Args:
        range: The largest resistance that is expected to be measured.
        current: The type of sense current to use.
        wires: The number of wires that are used for the resistance measurement.
    """

    range: int
    current: Literal["NORMAL", "ROOT2"]
    wires: Literal[3, 4]


@dataclass
class Voltage:
    """A channel configured to measure voltage.

    Args:
        rjc: The reference junction compensation type.
        thermocouple: The thermocouple type.
    """

    rjc: Literal["NONE", "INTERNAL"]
    thermocouple: Type | Literal["NONE"]


class Current:
    """Measure the current on channel 3."""


@dataclass
class MilliKDevice:
    """Information about a connected milliK device.

    Args:
        manufacturer: Manufacturer's name.
        model: Model number.
        serial: Serial number.
        firmware: Firmware revision number.
    """

    manufacturer: str
    model: str
    serial: str
    firmware: str


class MilliK(MultiMessageBased, manufacturer=r"Iso.*Tech.*", model=r"milli.*K.*", flags=re.IGNORECASE):
    """[IsoTech](https://isotech.co.uk/) milliK Precision Thermometer."""

    def __init__(self, equipment: Equipment) -> None:
        """[IsoTech](https://isotech.co.uk/) milliK Precision Thermometer.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Iso.*Tech.*"
        model=r"milli.*K.*"
        flags=IGNORECASE
        ```

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)
        self.rstrip: bool = True
        self.read_termination: bytes = b"\r"
        self.write_termination: bytes = b"\r"

        # REMOTE mode speeds up communication and is required for voltage measurements
        _ = self.write("MILLIK:REMOTE")

        devices, channels = _find_channel_numbers(self)

        # These are the strings that would be returned from each device by the *IDN? command
        # e.g. ['Isothermal Technology,millisKanner,21-P2593,2.01', 'Isothermal Technology,milliK,21-P2460,4.0.0']
        self._devices: list[MilliKDevice] = [MilliKDevice(*d.split(",")) for d in devices]

        self._channels: list[int] = channels

        self.channel_configuration: dict[int, Current | Resistance | Voltage] = {}
        """The channels that have been configured."""

    @property
    def channel_numbers(self) -> list[int]:
        """A list of available channel numbers.

        For example, [1, 2] for a single milliK or [1, 10, 11, 12, 13, 14, 15, 16, 17] for a milliK
        connected to a single millisKanner.
        """
        return self._channels

    @property
    def connected_devices(self) -> list[MilliKDevice]:
        """A list of information about the connected devices."""
        return self._devices

    @property
    def num_devices(self) -> int:
        """The number of connected devices."""
        return len(self._devices)

    def configure_current_measurement(self) -> None:
        """Configure the milliK to measure current on channel 3.

        The current is from a 4-20 mA transmitter on the rear of the milliK.
        """
        self.channel_configuration[3] = Current()

    def configure_resistance_measurement(
        self, channel: int, resistance: float, *, root2: bool = False, wire3: bool = False
    ) -> None:
        r"""Configure the milliK to measure resistance for the specified channel.

        Args:
            channel: The channel to configure for resistance measurements.
            resistance: The largest resistance value, in &Omega;, that is expected to be measured.
                The milliK selects the most sensitive range that can accommodate the specified value
                (up to 115 &Omega;, 460 &Omega; or 500 k&Omega; for the three supported ranges).
            root2: Use $\sqrt{2}$ mA sense current instead of the normal 1 mA sense current.
                Thermistors (resistance measurements in the 500 k&Omega; range) always use 2 μA.
            wire3: Whether the wiring arrangement is for 3 wires instead of the typical 4 wires.
        """
        if channel not in self._channels:
            msg = f"Channel {channel} is not available in the connected milliK devices"
            raise ValueError(msg)

        self.channel_configuration[channel] = Resistance(
            range=round(resistance), current="ROOT2" if root2 else "NORMAL", wires=3 if wire3 else 4
        )

    def configure_voltage_measurement(
        self, channel: int, *, rjc: bool = False, thermocouple: str | Type | None = None
    ) -> None:
        """Configure the milliK to measure voltage for the specified channel.

        Args:
            channel: The channel to configure for voltage measurements.
            rjc: Whether to use reference junction compensation for the measurements.
            thermocouple: The type of thermocouple that is used. If the `thermocouple` value is
                of type [str][], it must be a member name of the [Type][msl.equipment_resources.isotech.millik.Type]
                enumeration, e.g., `K`, `J`, `AU_PT`.
        """
        if channel not in self._channels:
            msg = f"Channel {channel} is not available in the connected milliK devices"
            raise ValueError(msg)

        self.channel_configuration[channel] = Voltage(
            rjc="INTERNAL" if rjc else "NONE",
            thermocouple="NONE" if thermocouple is None else to_enum(thermocouple, Type, to_upper=True),
        )

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Return the milliK device to LOCAL mode then disconnect from the device."""
        if not self._connected:
            return

        _ = self.write("MILLIK:LOCAL")
        super().disconnect()

    def read_all_channels(self, n: int = 1) -> Iterator[tuple[int, float]]:
        """Read from all configured channels.

        Args:
            n: The number of readings to average for each channel.

        Yields:
            The channel number and the average measurement value for that channel.
        """
        for c in sorted(self.channel_configuration):
            if n == 1:  # already a single float value
                yield c, self.read_channel(c)
            else:  # average multiple readings
                readings = self.read_channel(c, n=n)
                yield c, sum(readings) / len(readings)

    @overload
    def read_channel(self, channel: int, n: Literal[1] = 1) -> float: ...

    @overload
    def read_channel(self, channel: int, n: int) -> list[float]: ...

    def read_channel(self, channel: int, n: int = 1) -> float | list[float]:
        """Read a configured channel.

        Args:
            channel: The channel to read.
            n: The number of readings to acquire.

        Returns:
            A list of `n` readings or a single value if only one reading is requested.
        """
        cfg = self.channel_configuration.get(channel)
        if cfg is None:
            msg = f"Please first configure channel {channel} before attempting to read values"
            raise ValueError(msg)

        if isinstance(cfg, Resistance):
            commands = [
                f"SENSE:CHANNEL {channel}",
                "SENSE:FUNCTION RESISTANCE",
                f"SENSE:RESISTANCE:RANGE {cfg.range}",
                f"SENSE:RESISTANCE:WIRES {cfg.wires}",
                f"SENSE:CURRENT {cfg.current}",
            ]
        elif isinstance(cfg, Voltage):
            commands = [
                f"SENSE:CHANNEL {channel}",
                "SENSE:FUNCTION VOLTAGE",
                f"SENSE:PROBE {cfg.thermocouple}",
                f"SENSE:RJC {cfg.rjc}",
            ]
        else:
            commands = ["SENSE:CHANNEL 3", "SENSE:FUNCTION CURRENT"]

        commands.append(f"READ? {n}" if n > 1 else "READ?")
        reply = self.query(";".join(commands))

        try:
            readings = list(map(float, reply.split(",")))
        except ValueError:
            raise MSLConnectionError(self, f"Cannot map reply to float, {reply!r}") from None

        if len(readings) == 1:
            return readings[0]
        return readings


def _find_channel_numbers(instance: MessageBased) -> tuple[list[str], list[int]]:
    """Find the number of millisKanner Channel Expanders connected, if any, and hence the valid channel numbers.

    Up to 4 millisKanner can be connected to a single milliK.

    Returns a list of the connected devices and a list of the available channel numbers.
    """
    num_devices = 1
    channel_numbers = [1, 2]
    connected_devices = [instance.query("mill:list?")]  # returns only first line of string response
    while "milliK" not in connected_devices[-1].split(","):  # the last device will be the milliK
        connected_devices.append(instance.read())
        n = num_devices * 10
        channel_numbers.extend(range(n, n + 8))
        num_devices += 1

    if num_devices > 1:
        _ = channel_numbers.pop(1)  # removes channel 2 which is used to connect to the millisKanner daisy-chain

    return connected_devices, channel_numbers
