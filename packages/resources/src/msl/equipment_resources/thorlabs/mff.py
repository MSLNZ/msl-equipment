"""Communicate with a Motorised Filter Flip mount from Thorlabs."""

# cSpell: ignore MGMSG, OPERPARAMS
from __future__ import annotations

from dataclasses import dataclass
from struct import pack, unpack
from time import sleep
from typing import TYPE_CHECKING

from msl.equipment.schema import Interface

from .motion import ThorlabsMotion

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment

    from .motion import ThorlabsHardwareInfo


class MFF(Interface, manufacturer=r"Thorlabs", model=r"MFF"):
    """Communicate with a Motorised Filter Flip mount from Thorlabs."""

    unit: str = ""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a Motorised Filter Flip mount from Thorlabs.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"MFF"
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
                FlipperParameters(
                    transit_time=0.5,
                    dig1=FlipperIO(operating_mode=1, signal_mode=1, pulse_width=0.2),
                    dig2=FlipperIO(operating_mode=1, signal_mode=1, pulse_width=0.2),
                )
            )

    def disable(self) -> None:
        """Disable the motor so the Filter Flipper can be freely moved by hand."""
        self._motion.disable()

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the Filter Flipper."""
        if hasattr(self, "_motion"):
            self._motion.disconnect()

    def enable(self) -> None:
        """Enable the motor so the Filter Flipper is fixed in position."""
        self._motion.enable()

    def get_parameters(self) -> FlipperParameters:
        """Get the operating parameters.

        Returns:
            The transit time, digital I/O parameters for pin 1, digital I/O parameters for pin 2.
        """
        params = unpack("<HiiHHiHHiiI", self._motion.query(0x0511, param1=1, dest=0x50))  # MGMSG_MOT_REQ_MFF_OPERPARAMS
        o1, s1, pw1, o2, s2, pw2 = params[3:9]
        return FlipperParameters(float(params[1]), FlipperIO(o1, s1, pw1 * 1e-3), FlipperIO(o2, s2, pw2 * 1e-3))

    def hardware_info(self) -> ThorlabsHardwareInfo:
        """Get the hardware information.

        Returns:
            The hardware information about the Filter Flipper.
        """
        return self._motion.hardware_info()

    def identify(self) -> None:
        """Instruct Filter Flipper to identify itself by flashing its LED."""
        self._motion.identify()

    def is_enabled(self) -> bool:
        """Check if the motor is enabled.

        If enabled, power is applied to the motor so the Filter Flipper is fixed in position.

        Returns:
            Whether the motor is enabled or disabled.
        """
        return self._motion.is_enabled()

    def is_moving(self) -> bool:
        """Check if the Filter Flipper is moving.

        Returns:
            Whether the Filter Flipper is moving.
        """
        return bool(self.status() & 0x10)

    def move_to(self, position: int, *, wait: bool = True) -> None:
        """Move to a position.

        Args:
            position: The position to move to (either 1 or 2).
            wait: Whether to wait for the move to complete before returning to the calling program.
        """
        if position not in {1, 2}:
            msg = f"Invalid position {position}, must be 1 or 2"
            raise ValueError(msg)

        _ = self._motion.write(0x046A, param1=1, param2=position, dest=0x50)  # MGMSG_MOT_MOVE_JOG
        if wait:
            self.wait_until_moved()

    def position(self) -> int:
        """Get the position of the Filter Flipper, either 1 or 2 (or 0 if moving)."""
        status = self.status()
        if status & 0x01:  # forward (CW) hardware limit switch is active
            return 1
        if status & 0x02:  # reverse (CCW) hardware limit switch is active
            return 2
        return 0

    def set_parameters(self, parameters: FlipperParameters) -> None:
        """Set the operating parameters.

        Args:
            parameters: The operating parameters. It is recommended to call
                [get_parameters][msl.equipment_resources.thorlabs.mff.MFF.get_parameters]
                first and then update the appropriate attributes.
        """
        tt = round(parameters.transit_time * 1e3)
        tt_adc = round(10000000 * (tt**-1.591))
        data = pack(
            "<HiiHHiHHiiI",
            1,  # channel
            tt,
            tt_adc,
            parameters.dig1.operating_mode,
            parameters.dig1.signal_mode,
            round(parameters.dig1.pulse_width * 1e3),
            parameters.dig2.operating_mode,
            parameters.dig2.signal_mode,
            round(parameters.dig2.pulse_width * 1e3),
            0,  # not used
            0,  # not used
        )
        _ = self._motion.write(0x0510, data=data, dest=0x50)  # MGMSG_MOT_SET_MFF_OPERPARAMS

    def status(self) -> int:
        """Get the status of the Filter Flipper.

        Returns:
            The status.
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

    def toggle(self, *, wait: bool = True) -> None:
        """Toggle the position.

        If at position 1 then move to position 2 (and vice versa).

        Args:
            wait: Whether to wait for the move to complete before returning to the calling program.
        """
        position = 2 if self.position() == 1 else 1
        self.move_to(position, wait=wait)

    def wait_until_moved(self) -> None:
        """Wait until a move is complete."""
        sleep(0.02)  # Doesn't appear to be required, but allow time for the motor to update its status
        while self.is_moving():
            pass


@dataclass
class FlipperIO:
    """Filter flipper Digital I/O parameters.

    Attributes:
        operating_mode (int): The operating mode:

            * 1 &mdash; _Input_ Toggle position
            * 2 &mdash; _Input_ Go to position
            * 3 &mdash; _Output_ At position
            * 4 &mdash; _Output_ In motion

        signal_mode (int): Input/Output signal mode. The value depends on whether
            `operating_mode` is an _Input_ or an _Output_:

            If `operating_mode` is an _Input_

            * 1 &mdash; Button input
            * 2 &mdash; Logic edge input
            * 5 &mdash; Button input (swap position)
            * 6 &mdash; Logic edge input (swap position)

            If `operating_mode` is an _Output_

            * 16 &mdash; Logic level output
            * 32 &mdash; Logic pulse output
            * 80 &mdash; Logic level output (inverted)
            * 96 &mdash; Logic pulse output (inverted)

        pulse_width (float): The pulse width, in seconds. Valid range is between 0.01 and 65.535 seconds.
    """

    operating_mode: int
    signal_mode: int
    pulse_width: float


@dataclass
class FlipperParameters:
    """Filter Flipper parameters.

    Attributes:
        transit_time (float): The time taken (in seconds) for the flipper to move from position 1
            to position 2 and vice versa. The value must be in the range 0.3 to 2.8 seconds.
        dig1 (FlipperIO): Digital I/O parameters for pin 1.
        dig2 (FlipperIO): Digital I/O parameters for pin 2.
    """

    transit_time: float
    dig1: FlipperIO
    dig2: FlipperIO

    def __post_init__(self) -> None:
        """Check values are within allowed ranges."""
        if self.transit_time < 0.3 or self.transit_time > 2.8:  # noqa: PLR2004
            msg = f"Invalid transit time {self.transit_time}, must be in the range 0.3 to 2.8 seconds"
            raise ValueError(msg)

        for pw in (self.dig1.pulse_width, self.dig2.pulse_width):
            if pw < 0.01 or pw > 65.535:  # noqa: PLR2004
                msg = f"Invalid Digital I/O pulse width {pw}, must be in the range 0.01 to 65.535 seconds"
                raise ValueError(msg)
