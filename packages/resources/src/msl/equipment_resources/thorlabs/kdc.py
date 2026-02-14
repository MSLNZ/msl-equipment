"""Communicate with a KDC101 motion controller from Thorlabs."""

# cSpell: ignore MGMSG PRMT PRMTZ
from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment.interfaces.message_based import MSLConnectionError

from .motion import (
    Convert,
    ThorlabsHomeParameters,
    ThorlabsLimitParameters,
    ThorlabsMotion,
    ThorlabsMoveParameters,
    find_device,
)

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class KDC(ThorlabsMotion, manufacturer=r"Thorlabs", model=r"KDC"):
    """Communicate with a KDC101 motion controller from Thorlabs."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a KDC101 motion controller from Thorlabs.

        The Z8, Z9 and PRM series of actuators/stages are supported.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"KDC"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for a `KDC` motion controller, as well as the _properties_ defined in
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

        self.unit: str
        if "PRMT" in device:  # must come before PRM and Z8 checks, model number could be PRMTZ8 or PRMTZ8/M
            pitch = 18.0
            steps_per_rev = 512.0
            gearbox_ratio = 67.49016
            self.unit = "\u00b0"
        elif "PRM" in device:  # must come before Z8 check, model number could be PRM1Z8 or PRM1/MZ8
            pitch = 17.87
            steps_per_rev = 512.0
            gearbox_ratio = 67.0
            self.unit = "\u00b0"
        elif ("Z8" in device) or ("Z9" in device):  # also valid for MTSxx-Z8 translation stages
            pitch = 1.0
            steps_per_rev = 512.0
            gearbox_ratio = 67.49016
        else:
            msg = f"The actuator/stage {device!r} is not currently supported, only Z8, Z9 and PRM series are supported"
            raise MSLConnectionError(self, msg)

        # Conversion factors must be defined before initialising the default parameters below
        t = 2048.0 / 6e6
        enc_cnt = (steps_per_rev * gearbox_ratio) / pitch
        self._position: Convert = Convert(1.0 / enc_cnt)
        self._velocity: Convert = Convert(1.0 / (enc_cnt * t * 65536.0), decimals=3)
        self._acceleration: Convert = Convert(1.0 / (enc_cnt * t * t * 65536.0), decimals=3)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false

        if self._init_defaults:
            if "PRM" in device:  # check must come first, since model number could be PRM1Z8 or PRM1/MZ8
                _init_prmt_prm(self)
            elif "MTS" in device:
                _init_mts(self)
            else:
                _init_z8_z9(self)


def _init_prmt_prm(kdc: KDC) -> None:
    kdc.set_backlash(1.0)
    kdc.set_move_parameters(
        ThorlabsMoveParameters(
            channel=1,
            min_velocity=0.0,
            max_velocity=10.0,
            acceleration=10.0,
        )
    )
    kdc.set_home_parameters(
        ThorlabsHomeParameters(
            channel=1,
            direction="reverse",  # HomeDir 2
            limit_switch="reverse",  # HomeLimitSwitch 1
            velocity=10.0,
            offset=4.0,
        )
    )
    kdc.set_limit_parameters(
        ThorlabsLimitParameters(
            channel=1,
            cw_hardware=4,
            ccw_hardware=1,
            cw_software=1.0,
            ccw_software=1.0,
            mode=1,
        )
    )


def _init_z8_z9(kdc: KDC) -> None:
    kdc.set_backlash(0.3)
    kdc.set_move_parameters(
        ThorlabsMoveParameters(
            channel=1,
            min_velocity=0.0,
            max_velocity=2.3,
            acceleration=1.5,
        )
    )
    kdc.set_home_parameters(
        ThorlabsHomeParameters(
            channel=1,
            direction="reverse",  # HomeDir 2
            limit_switch="reverse",  # HomeLimitSwitch 1
            velocity=1.0,
            offset=0.3,
        )
    )
    kdc.set_limit_parameters(
        ThorlabsLimitParameters(
            channel=1,
            cw_hardware=2,
            ccw_hardware=2,
            cw_software=3.0,
            ccw_software=1.0,
            mode=1,
        )
    )


def _init_mts(kdc: KDC) -> None:
    kdc.set_backlash(0.05)
    kdc.set_move_parameters(
        ThorlabsMoveParameters(
            channel=1,
            min_velocity=0.0,
            max_velocity=2.4,
            acceleration=1.5,
        )
    )
    kdc.set_home_parameters(
        ThorlabsHomeParameters(
            channel=1,
            direction="reverse",  # HomeDir 2
            limit_switch="reverse",  # HomeLimitSwitch 1
            velocity=1.0,
            offset=1.0,
        )
    )
    kdc.set_limit_parameters(
        ThorlabsLimitParameters(
            channel=1,
            cw_hardware=2,
            ccw_hardware=2,
            cw_software=3.0,
            ccw_software=1.0,
            mode=1,
        )
    )
