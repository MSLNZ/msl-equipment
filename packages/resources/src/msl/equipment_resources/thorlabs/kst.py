"""Communicate with a KST101 or KST201 motion controller from Thorlabs."""

# cSpell: ignore MGMSG TSTACTUATORTYPE
from __future__ import annotations

import re
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


class KST(ThorlabsMotion, manufacturer=r"Thorlabs", model=r"KST"):
    """Communicate with a KST101 or KST201 motion controller from Thorlabs."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a KST101 or KST201 motion controller from Thorlabs.

        The ZFS and ZST series of actuators are supported.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Thorlabs"
        model=r"KST"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for a `KST` motion controller, as well as the _properties_ defined in
        [ThorlabsMotion][msl.equipment_resources.thorlabs.motion.ThorlabsMotion].

        Attributes: Connection Properties:
            actuator (str | None): The actuator that is attached to the motion controller.
                If not specified, the value is looked up in a file that is managed by
                Thorlabs software. If the Thorlabs file cannot be found, an exception is
                raised. _Default: `None`_
        """
        super().__init__(equipment)

        device = find_device(equipment)
        if not device:
            msg = (
                "Cannot determine the actuator that is attached to the motion controller. "
                "Specify an 'actuator' key in the Connection properties with the value as "
                "the model number of the actuator that is attached to the motion controller."
            )
            raise MSLConnectionError(self, msg)

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false

        if "ZFS" in device:
            #  6mm: ZFS06
            # 13mm: ZFS13, ZFS13B
            # 25mm: ZFS25B
            actuators = {6: 0x40, 13: 0x41, 25: 0x42}

            steps = 24.0 * 2048.0 * 400.0 / 9.0
            self._position: Convert = Convert(1.0 / steps)
            self._velocity: Convert = Convert(1.0 / (steps * 53.68), decimals=3)
            self._acceleration: Convert = Convert((1.0 * 90.9) / steps, decimals=3)

            if self._init_defaults:
                _init_zfs(self)

        elif "ZST" in device:
            #  6mm: ZST206, ZST6B, ZST6
            # 13mm: ZST213B, ZST213, ZST13B, ZST13
            # 25mm: ZST225B, ZST25B, ZST25
            actuators = {6: 0x30, 206: 0x30, 13: 0x31, 213: 0x31, 25: 0x32, 225: 0x32}

            steps = 24.0 * 2048.0 * 40.866
            self._position = Convert(1.0 / steps, decimals=6)
            self._velocity = Convert(1.0 / (steps * 53.68), decimals=3)
            self._acceleration = Convert((1.0 * 90.9) / steps, decimals=3)

            if self._init_defaults:
                _init_zst(self)

        else:
            msg = f"The actuator {device!r} is not currently supported, only ZFS and ZST series are supported"
            raise MSLConnectionError(self, msg)

        match = re.search(r"(?P<number>\d+)", device)
        actuator = None if match is None else actuators.get(int(match["number"]))
        if actuator is None:
            msg = f"Do not know how to configure the actuator type for {device!r}"
            raise MSLConnectionError(self, msg)

        _ = self.write(0x04FE, param1=actuator, dest=0x50)  # MGMSG_MOT_SET_TSTACTUATORTYPE


def _init_zfs(kst: KST) -> None:
    kst.set_backlash(0.02)
    kst.set_move_parameters(
        ThorlabsMoveParameters(
            channel=1,
            min_velocity=0.0,
            max_velocity=1.5,
            acceleration=1.0,
        )
    )
    kst.set_home_parameters(
        ThorlabsHomeParameters(
            channel=1,
            direction="reverse",  # HomeDir 2
            limit_switch="reverse",  # HomeLimitSwitch 1
            velocity=0.5,
            offset=0.1,
        )
    )
    kst.set_limit_parameters(
        ThorlabsLimitParameters(
            channel=1,
            cw_hardware=2,
            ccw_hardware=2,
            cw_software=3.0,
            ccw_software=1.0,
            mode=1,
        )
    )


def _init_zst(kst: KST) -> None:
    kst.set_backlash(0.02)
    kst.set_move_parameters(
        ThorlabsMoveParameters(
            channel=1,
            min_velocity=0.0,
            max_velocity=1.0,
            acceleration=0.5,
        )
    )
    kst.set_home_parameters(
        ThorlabsHomeParameters(
            channel=1,
            direction="reverse",  # HomeDir 2
            limit_switch="reverse",  # HomeLimitSwitch 1
            velocity=0.5,
            offset=0.1,
        )
    )
    kst.set_limit_parameters(
        ThorlabsLimitParameters(
            channel=1,
            cw_hardware=2,
            ccw_hardware=2,
            cw_software=3.0,
            ccw_software=1.0,
            mode=1,
        )
    )
