"""Communicate with a K-Cube Solenoid Controller from Thorlabs."""

# cSpell: ignore Hiii
from __future__ import annotations

from dataclasses import dataclass
from struct import pack, unpack
from typing import TYPE_CHECKING

from msl.equipment.schema import Interface

from .motion import ThorlabsMotion

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment

    from .motion import ThorlabsHardwareInfo


class KSC(Interface, manufacturer=r"Thorlabs", model=r"KSC"):
    """Communicate with a K-Cube Solenoid Controller from Thorlabs."""

    unit: str = ""

    MANUAL: int = 1
    """Manual operating mode."""

    SINGLE: int = 2
    """Single operating mode."""

    AUTO: int = 3
    """Auto operating mode."""

    TRIGGER: int = 4
    """Trigger operating mode."""

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
            self.set_parameters(
                ThorlabsSolenoidParameters(
                    operating_mode=1,
                    on_duration=0.488,
                    off_duration=0.488,
                    cycle_count=10000,
                )
            )

    def disable(self) -> None:
        """Disable the Solenoid Controller."""
        self._motion.disable()

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the Solenoid Controller."""
        if hasattr(self, "_motion"):
            self._motion.disconnect()

    def enable(self) -> None:
        """Enable the Solenoid Controller."""
        self._motion.enable()

    def hardware_info(self) -> ThorlabsHardwareInfo:
        """Get the hardware information.

        Returns:
            The hardware information about the Solenoid Controller.
        """
        return self._motion.hardware_info()

    def identify(self) -> None:
        """Instruct Solenoid Controller to identify itself by flashing its LED."""
        self._motion.identify()

    def is_enabled(self) -> bool:
        """Check if the Solenoid Controller is enabled.

        Returns:
            Whether the Solenoid Controller is enabled or disabled.
        """
        return self._motion.is_enabled()

    def get_parameters(self) -> ThorlabsSolenoidParameters:
        """Get the operating parameters of the Solenoid Controller."""
        mode = self._motion.query(0x04C1, param1=1, dest=0x50)[1]
        _, on, off, n = unpack("<Hiii", self._motion.query(0x04C4, param1=1, dest=0x50))
        return ThorlabsSolenoidParameters(
            operating_mode=mode, on_duration=on * 1e-3, off_duration=off * 1e-3, cycle_count=n
        )

    def set_parameters(self, parameters: ThorlabsSolenoidParameters) -> None:
        """Set the operating parameters of the Solenoid Controller.

        Args:
            parameters: The operating parameters. It is recommended to call
                [get_parameters][msl.equipment_resources.thorlabs.ksc.KSC.get_parameters]
                first and then update the appropriate attributes.
        """
        cycle_data = pack(
            "<Hiii",
            1,
            round(parameters.on_duration * 1e3),
            round(parameters.off_duration * 1e3),
            parameters.cycle_count,
        )
        _ = self._motion.write(0x04C0, param1=1, param2=parameters.operating_mode, dest=0x50)
        _ = self._motion.write(0x04C3, data=cycle_data, dest=0x50)

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
class ThorlabsSolenoidParameters:
    """Parameters of the Solenoid Controller.

    Attributes:
        operating_mode (int): The operating mode of the solenoid. The value must be of

            * `1` &mdash; MANUAL
            * `2` &mdash; SINGLE
            * `3` &mdash; AUTO
            * `4` &mdash; TRIGGER

        on_duration (float): The time, in seconds, which the solenoid is activated. Must be between
            0.01 and 10k seconds (accurate to the nearest ms). This parameter is ignored if operating
            in MANUAL mode.
        off_duration (float): The time, in seconds, which the solenoid is deactivated. Must be between
            0.01 and 10k seconds (accurate to the nearest ms). This parameter is ignored if operating
            in MANUAL mode.
        cycle_count (int): If the controller is operating in AUTO or TRIGGER mode, this parameter
            specifies the number of open/close cycles to perform. The value can be from 0 to 1 million.
            If set to 0 the controller cycles indefinitely. If the controller is operating in MANUAL
            or SINGLE mode, this parameter is ignored.
    """

    operating_mode: int
    on_duration: float
    off_duration: float
    cycle_count: int

    def __post_init__(self) -> None:
        """Check values are within allowed ranges."""
        if self.operating_mode not in (1, 2, 3, 4):
            msg = f"Invalid solenoid operating mode, {self.operating_mode}, must be 1, 2, 3 or 4"
            raise ValueError(msg)

        for duration in (self.on_duration, self.off_duration):
            if duration < 0.01 or duration > 10e3:  # noqa: PLR2004
                msg = f"Invalid solenoid on/off duration, {duration}, must be between 0.01 and 10k seconds"
                raise ValueError(msg)

        if self.cycle_count < 0 or self.cycle_count > 1_000_000:  # noqa: PLR2004
            msg = f"Invalid solenoid cycle count, {self.cycle_count}, must be between 0 and 1M"
            raise ValueError(msg)
