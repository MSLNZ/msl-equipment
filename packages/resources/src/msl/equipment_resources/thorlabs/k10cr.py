"""Communicate with a K10CR1 or K10CR2 device from Thorlabs.."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .thorlabs import Convert, Thorlabs, ThorlabsHomeParameters, ThorlabsLimitParameters, ThorlabsMoveParameters

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class K10CR(Thorlabs, manufacturer=r"Thorlabs", model=r"K10CR[12]"):
    """Communicate with a K10CR1 or K10CR2 device from Thorlabs."""

    unit: str = "\u00b0"
    """The real-world unit."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a K10CR1 or K10CR2 device from Thorlabs.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"K10CR[12]"
        ```

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false
        self._position_message_id: int = 0x0411

        # 200 steps per revolution
        # 2048 micro-steps per full step
        # 120:1 reduction gearbox
        steps = float(200 * 2048 * 120)
        self._position: Convert = Convert(360.0 / steps)
        self._velocity: Convert = Convert(360.0 / (steps * 53.68), decimals=3)
        self._acceleration: Convert = Convert((360.0 * 90.9) / steps, decimals=3)

        self.set_backlash(1.0)
        self.set_move_parameters(
            ThorlabsMoveParameters(
                channel=1,
                min_velocity=0.0,
                max_velocity=10.0,
                acceleration=10.0,
            )
        )
        self.set_home_parameters(
            ThorlabsHomeParameters(
                channel=1,
                direction="reverse",  # HomeDir 2
                limit_switch="reverse",  # HomeLimitSwitch 1
                velocity=10.0,
                offset=4.0,
            )
        )
        self.set_limit_parameters(
            ThorlabsLimitParameters(
                channel=1,
                cw_hardware=4,
                ccw_hardware=1,
                cw_software=1.0,
                ccw_software=1.0,
                mode=1,
            )
        )
