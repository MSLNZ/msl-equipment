"""Communicate with a Long Travel Stage (Integrated Controller) from Thorlabs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .motion import Convert, ThorlabsHomeParameters, ThorlabsLimitParameters, ThorlabsMotion, ThorlabsMoveParameters

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class LTS(ThorlabsMotion, manufacturer=r"Thorlabs", model=r"LTS"):
    """Communicate with a Long Travel Stage (Integrated Controller) from Thorlabs."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a Long Travel Stage (Integrated Controller) from Thorlabs.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"LTS"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the _properties_
        that are defined in [ThorlabsMotion][msl.equipment_resources.thorlabs.motion.ThorlabsMotion].
        """
        super().__init__(equipment)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false

        micro_steps = 2048.0 if self.hardware_info().hardware_version >= 3 else 128.0  # noqa: PLR2004
        steps = 200.0 * micro_steps  # 200 steps per revolution
        self._position: Convert = Convert(1.0 / steps)
        self._velocity: Convert = Convert(1.0 / (steps * 53.68), decimals=3)
        self._acceleration: Convert = Convert((1.0 * 90.9) / steps, decimals=3)

        if self._init_defaults:
            self.set_backlash(0.05)
            self.set_move_parameters(
                ThorlabsMoveParameters(
                    channel=1,
                    min_velocity=0.0,
                    max_velocity=20.0,
                    acceleration=20.0,
                )
            )
            self.set_home_parameters(
                ThorlabsHomeParameters(
                    channel=1,
                    direction="reverse",  # HomeDir 2
                    limit_switch="reverse",  # HomeLimitSwitch 1
                    velocity=2.0,
                    offset=0.5,
                )
            )
            self.set_limit_parameters(
                ThorlabsLimitParameters(
                    channel=1,
                    cw_hardware=2,
                    ccw_hardware=2,
                    cw_software=3.0,
                    ccw_software=1.0,
                    mode=1,
                )
            )
