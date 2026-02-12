"""Communicate with a K10CR1 or K10CR2 rotation stage from Thorlabs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .motion import Convert, ThorlabsHomeParameters, ThorlabsLimitParameters, ThorlabsMotion, ThorlabsMoveParameters

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class K10CR(ThorlabsMotion, manufacturer=r"Thorlabs", model=r"K10CR"):
    """Communicate with a K10CR1 or K10CR2 rotation stage from Thorlabs."""

    unit: str = "\u00b0"
    """The physical unit."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a K10CR1 or K10CR2 rotation stage from Thorlabs.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"K10CR"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the _properties_
        that are defined in [ThorlabsMotion][msl.equipment_resources.thorlabs.motion.ThorlabsMotion].
        """
        super().__init__(equipment)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false
        self._position_message_id: int = 0x0411

        # 200 steps per revolution
        # 2048 micro-steps per full step
        # 120:1 reduction gearbox
        steps = float(200 * 2048 * 120)
        self._position: Convert = Convert(360.0 / steps, decimals=5)
        self._velocity: Convert = Convert(360.0 / (steps * 53.68), decimals=3)
        self._acceleration: Convert = Convert((360.0 * 90.9) / steps, decimals=3)

        if self._init_defaults:
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
