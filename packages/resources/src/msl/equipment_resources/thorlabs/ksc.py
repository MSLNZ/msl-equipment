"""Communicate with a K-Cube Solenoid Controller from Thorlabs."""

# cSpell: ignore Hiii
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from struct import pack, unpack
from typing import TYPE_CHECKING

from msl.equipment.schema import Interface
from msl.equipment.utils import to_enum

from .motion import ThorlabsMotion

if TYPE_CHECKING:
    from collections.abc import Iterator

    from msl.equipment.schema import Equipment

    from .motion import ThorlabsHardwareInfo


class KSC(Interface, manufacturer=r"Thorlabs", model=r"KSC"):
    """Communicate with a K-Cube Solenoid Controller from Thorlabs."""

    unit: str = ""

    class OperatingMode(IntEnum):
        """Solenoid operating mode.

        Attributes:
            MANUAL (int): Upon calling [open_shutter][msl.equipment_resources.thorlabs.ksc.KSC.open_shutter]
                the shutter remains open until [close_shutter][msl.equipment_resources.thorlabs.ksc.KSC.close_shutter]
                is called.
            SINGLE (int): Upon calling [open_shutter][msl.equipment_resources.thorlabs.ksc.KSC.open_shutter]
                the shutter remains open for `on_duration` seconds,
                see [set_cycle_parameters][msl.equipment_resources.thorlabs.ksc.KSC.set_cycle_parameters], and
                then closes. The shutter can also be closed by rotating the wheel on the controller
                downwards before `on_duration` elapses.
            AUTO (int): The shutter will open for `on_duration` seconds then close for `off_duration` seconds
                and repeat between open/close states `cycle_count` times, see
                [set_cycle_parameters][msl.equipment_resources.thorlabs.ksc.KSC.set_cycle_parameters].
            TRIGGERED (int): In triggered mode, a rising/falling edge on a configured TRIG input will
                open the shutter, which will remain open until a falling/rising edge is detected,
                see [set_trigger_parameters][msl.equipment_resources.thorlabs.ksc.KSC.set_trigger_parameters].
        """

        MANUAL = 1
        SINGLE = 2
        AUTO = 3
        TRIGGERED = 4

    class TriggerMode(IntEnum):
        """Solenoid trigger I/O mode.

        Attributes:
            DISABLED (int): TRIG port is not used. `0`
            INPUT (int): Digital input. `1`
            OUTPUT (int): Digital output. `10`
        """

        DISABLED = 0
        INPUT = 1
        OUTPUT = 10

    class TriggerPolarity(IntEnum):
        """Solenoid trigger polarity mode.

        Attributes:
            HIGH (int): Active high. `1`
            LOW (int): Active low. `2`
        """

        HIGH = 1
        LOW = 2

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a K-Cube Solenoid Controller from Thorlabs.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"KSC"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the _properties_
        that are defined in [ThorlabsMotion][msl.equipment_resources.thorlabs.motion.ThorlabsMotion].
        """
        super().__init__(equipment)

        self._motion: ThorlabsMotion = ThorlabsMotion(equipment)

        if self._motion._init_defaults:  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            self.operating_mode = KSC.OperatingMode.MANUAL
            self.set_cycle_parameters()
            self.set_display_parameters()
            self.set_trigger_parameters()

    def close_shutter(self) -> None:
        """Close the shutter.

        !!! note
            It is not possible to query whether the shutter is open or closed.
        """
        _ = self._motion.write(0x04CB, param1=1, param2=2, dest=0x50)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the Solenoid Controller."""
        if hasattr(self, "_motion"):
            self._motion.disconnect()

    def get_cycle_parameters(self) -> KSCCycleParameters:
        """Get the cycle parameters of the Solenoid Controller.

        Returns:
            The cycle parameters.
        """
        _, on, off, n = unpack("<Hiii", self._motion.query(0x04C4, param1=1, dest=0x50))
        return KSCCycleParameters(on_duration=on * 1e-3, off_duration=off * 1e-3, cycle_count=n)

    def get_display_parameters(self) -> KSCDisplayParameters:
        """Get the LED display parameters of the Solenoid Controller.

        Returns:
            The LED display parameters.
        """
        _, i, d, t = unpack("<H20x3H8x", self._motion.query(0x0521, param1=1, dest=0x50))
        return KSCDisplayParameters(intensity=i, dimmed=d, timeout=t)

    def get_trigger_parameters(self) -> tuple[TriggerMode, TriggerPolarity, TriggerMode, TriggerPolarity]:
        """Get the trigger parameters for the `TRIG1` and `TRIG2` ports.

        Returns:
            The `(TRIG1 mode, TRIG1 polarity, TRIG2 mode, TRIG2 polarity)` parameters.
        """
        _, m1, p1, m2, p2 = unpack("<5H12x", self._motion.query(0x0524, param1=1, dest=0x50))
        return KSC.TriggerMode(m1), KSC.TriggerPolarity(p1), KSC.TriggerMode(m2), KSC.TriggerPolarity(p2)

    def hardware_info(self) -> ThorlabsHardwareInfo:
        """Get the hardware information.

        Returns:
            The hardware information about the Solenoid Controller.
        """
        return self._motion.hardware_info()

    def identify(self) -> None:
        """Instruct the Solenoid Controller to identify itself by flashing its LED display."""
        self._motion.identify()

    @property
    def interlock_mode(self) -> bool:
        """Get/set the interlock mode.

        Whether the hardware interlock is required (`True`) or not required (`False`).
        """
        data = self._motion.query(0x04C7, param1=1, dest=0x50)
        return data[1] == 1

    @interlock_mode.setter
    def interlock_mode(self, mode: bool) -> None:
        _ = self._motion.write(0x04C6, param1=1, param2=1 if mode else 2, dest=0x50)

    def is_key_unlocked(self) -> bool:
        """Get the state of the safety key.

        Returns:
            Whether the safety key is in the locked (`False`) or unlocked (`True`) position.
        """
        return bool(self.status() & (1 << 13))

    def open_shutter(self) -> None:
        """Open the shutter.

        !!! note
            It is not possible to query whether the shutter is open or closed.
        """
        _ = self._motion.write(0x04CB, param1=1, param2=1, dest=0x50)

    @property
    def operating_mode(self) -> OperatingMode:
        """Get/set the operating mode of the Solenoid Controller."""
        data = self._motion.query(0x04C1, param1=1, dest=0x50)
        return KSC.OperatingMode(data[1])

    @operating_mode.setter
    def operating_mode(self, mode: OperatingMode) -> None:
        _ = self._motion.write(0x04C0, param1=1, param2=mode, dest=0x50)

    def set_cycle_parameters(
        self, on_duration: float = 0.5, off_duration: float = 0.5, cycle_count: float = 10_000
    ) -> None:
        """Set the cycle parameters of the Solenoid Controller.

        Args:
            on_duration (float): The time, in seconds, that the shutter is open. The value must
                be between 0.01 and 10k seconds (accurate to the nearest ms). This parameter is
                not used if the [OperatingMode][msl.equipment_resources.thorlabs.ksc.KSC.OperatingMode]
                is `MANUAL` or `TRIGGERED` .
            off_duration (float): The time, in seconds, that the shutter is closed. The value must be
                between 0.01 and 10k seconds (accurate to the nearest ms). This parameter is only used
                if the [OperatingMode][msl.equipment_resources.thorlabs.ksc.KSC.OperatingMode] is `AUTO`.
            cycle_count (float): The number of open/close cycles to perform, only if the
                [OperatingMode][msl.equipment_resources.thorlabs.ksc.KSC.OperatingMode] is `AUTO`.
                The value can be any integer from 0 to 1 million. If set to 0, the controller cycles indefinitely.
        """
        for duration in (on_duration, off_duration):
            if duration < 0.01 or duration > 10e3:  # noqa: PLR2004
                msg = f"Invalid solenoid on/off duration, {duration}, must be between 0.01 and 10k seconds"
                raise ValueError(msg)

        if cycle_count < 0 or cycle_count > 1e6:  # noqa: PLR2004
            msg = f"Invalid solenoid cycle count, {cycle_count}, must be between 0 and 1M"
            raise ValueError(msg)

        data = pack("<Hiii", 1, round(on_duration * 1e3), round(off_duration * 1e3), int(cycle_count))
        _ = self._motion.write(0x04C3, data=data, dest=0x50)

    def set_display_parameters(self, intensity: int = 50, dimmed: int = 5, timeout: int = 2) -> None:
        """Set the LED display parameters of the Solenoid Controller.

        Args:
            intensity (int): LED display intensity, as a percentage [0, 100].
            dimmed (int): Percentage of the full intensity to dim the LED display.
                The value must be between 0 (off) to 10 (brightest).
            timeout (int): The number of minutes of inactivity after which the intensity is dimmed.
                The value must be in the range [0, 480]. Set to 0 to disable dimming.
        """
        if intensity < 0 or intensity > 100:  # noqa: PLR2004
            msg = f"Invalid solenoid display intensity, {intensity}, must be between 0 and 100"
            raise ValueError(msg)

        if dimmed < 0 or dimmed > 10:  # noqa: PLR2004
            msg = f"Invalid solenoid display dimmed intensity, {dimmed}, must be between 0 and 10"
            raise ValueError(msg)

        if timeout < 0 or timeout > 480:  # noqa: PLR2004
            msg = f"Invalid solenoid display timeout, {timeout}, must be between 0 and 480"
            raise ValueError(msg)

        data = pack("<H20x3H8x", 1, intensity, dimmed, timeout)
        _ = self._motion.write(0x0520, data=data, dest=0x50)

    def set_trigger_parameters(
        self,
        mode1: TriggerMode | int | str = "INPUT",
        polarity1: TriggerPolarity | int | str = "HIGH",
        mode2: TriggerMode | int | str = "OUTPUT",
        polarity2: TriggerPolarity | int | str = "HIGH",
    ) -> None:
        """Set the trigger parameters for the `TRIG1` and `TRIG2` ports.

        Args:
            mode1: `TRIG1` mode. Can be an enum member name (case insensitive) or value.
            polarity1: `TRIG1` polarity. Can be an enum member name (case insensitive) or value.
            mode2: `TRIG2` mode. Can be an enum member name (case insensitive) or value.
            polarity2: `TRIG2` polarity. Can be an enum member name (case insensitive) or value.
        """
        m1 = to_enum(mode1, KSC.TriggerMode, to_upper=True)
        p1 = to_enum(polarity1, KSC.TriggerPolarity, to_upper=True)
        m2 = to_enum(mode2, KSC.TriggerMode, to_upper=True)
        p2 = to_enum(polarity2, KSC.TriggerPolarity, to_upper=True)
        data = pack("<5H12x", 1, m1, p1, m2, p2)
        _ = self._motion.write(0x0523, data=data, dest=0x50)

    def status(self) -> int:
        """Get the status of the Solenoid Controller.

        Returns:
            The status. A 32-bit value that represents the current status of the motion controller.
                Each of the 32 bits acts as a flag (0 or 1), simultaneously indicating 32 distinct
                operating conditions of the motion controller.
        """
        return self._motion.status()

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for [read][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.read]
        and [write][msl.equipment_resources.thorlabs.motion.ThorlabsMotion.write] operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """  # noqa: D205
        return self._motion.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._motion.timeout = value


@dataclass
class KSCCycleParameters:
    """Cycle parameters of the Solenoid Controller.

    Attributes:
        on_duration (float): The time, in seconds, that the shutter is open.
        off_duration (float): The time, in seconds, that the shutter is closed.
        cycle_count (int): The number of open/close cycles to perform.
            If 0, the controller cycles indefinitely.
    """

    on_duration: float
    off_duration: float
    cycle_count: int

    def __iter__(self) -> Iterator[float]:
        """Returns an iterator over the parameters."""
        return iter((self.on_duration, self.off_duration, self.cycle_count))


@dataclass
class KSCDisplayParameters:
    """LED display parameters of the Solenoid Controller.

    Attributes:
        intensity (int): LED display intensity, as a percentage.
        dimmed (int): Percentage of the full intensity to dim the LED display.
        timeout (int): The number of minutes of inactivity after which the intensity is dimmed.
            If 0, dimming is disable.
    """

    intensity: int
    dimmed: int
    timeout: int

    def __iter__(self) -> Iterator[int]:
        """Returns an iterator over the parameters."""
        return iter((self.intensity, self.dimmed, self.timeout))
