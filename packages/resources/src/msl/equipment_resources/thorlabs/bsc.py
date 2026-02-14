"""Communicate with a BSC20x Series motion controller from Thorlabs."""

# cSpell: ignore MGMSG TSTACTUATORTYPE
from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment.interfaces.message_based import MSLConnectionError

from .motion import Convert, ThorlabsMotion, find_device

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class BSC(ThorlabsMotion, manufacturer=r"Thorlabs", model=r"BSC2"):
    """Communicate with a BSC20x Series motion controller from Thorlabs."""

    def __init__(self, equipment: Equipment) -> None:  # noqa: C901, PLR0912
        """Communicate with a BSC20x Series motion controller from Thorlabs.

        The NR360S or HDR50 rotation stage, DRV series of actuators and the NRT
        series of translation stages are supported.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"BSC2"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for a `BSC` motion controller, as well as the _properties_ defined in
        [ThorlabsMotion][msl.equipment_resources.thorlabs.motion.ThorlabsMotion].

        Attributes: Connection Properties:
            actuator (str | None): The actuator that is attached to the motion controller.
                If not specified, the value is looked up in a file that is managed by
                Thorlabs software. If the Thorlabs file cannot be found, an exception is
                raised. _Default: `None`_
            stage (str | None): Alias for `actuator`.
        """
        super().__init__(equipment)

        device = find_device(equipment)
        if not device:
            msg = (
                "Cannot determine the actuator/stage that is attached to the motion controller. "
                "Specify an 'actuator' or 'stage' key in the Connection properties with the value as "
                "the model number of the actuator or stage that is attached to the motion controller."
            )
            raise MSLConnectionError(self, msg)

        if self._init_defaults:
            msg = (
                "Specifying init=True in the Connection properties is not supported for a BSC20x Series "
                "controller. Call the class methods to set the motor parameters for a particular channel "
                "or use Thorlabs software to persist the parameters."
            )
            raise ValueError(msg)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false

        # Many of the device names could include HS or /M so use "in" instead of "=="
        actuator_type = 0
        steps = 200.0 * 2048.0
        if ("NR360S" in device) or ("HDR50" in device):
            self.unit: str = "\u00b0"
            steps /= 5.45454
            if "HDR50" in device:
                actuator_type = 0xAF
        elif "DRV001" in device:
            steps /= 0.5
        elif "DRV013" in device:
            actuator_type = 0x50
        elif "DRV014" in device:
            actuator_type = 0x51
        elif "DRV208" in device:
            steps /= 0.5
            actuator_type = 0xB2
        elif "DRV225" in device:
            actuator_type = 0xB0
        elif "DRV250" in device:
            actuator_type = 0xB1
        elif "NRT100" in device:
            actuator_type = 0xB3
        elif "NRT150" in device:
            actuator_type = 0xB4
        else:
            msg = f"The actuator/stage {device!r} is not currently supported"
            raise MSLConnectionError(self, msg)

        self._position: Convert = Convert(1.0 / steps)
        self._velocity: Convert = Convert(1.0 / (steps * 53.68), decimals=3)
        self._acceleration: Convert = Convert((1.0 * 90.9) / steps, decimals=3)

        if actuator_type > 0:
            _ = self.write(0x04FE, param1=actuator_type, dest=0x50)  # MGMSG_MOT_SET_TSTACTUATORTYPE
