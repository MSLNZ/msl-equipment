"""Communicate with a KST101 or KST201 motor controller from Thorlabs."""

# cSpell: ignore MGMSG TSTACTUATORTYPE
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from msl.equipment.interfaces.message_based import MSLConnectionError

from .thorlabs import (
    Convert,
    Thorlabs,
    ThorlabsHomeParameters,
    ThorlabsLimitParameters,
    ThorlabsMoveParameters,
    find_device,
)

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class KST(Thorlabs, manufacturer=r"Thorlabs", model=r"KST"):
    """Communicate with a KST101 or KST201 motor controller from Thorlabs."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a KST101 or KST201 motor controller from Thorlabs.

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
        _properties_ for a KST motor controller, as well as the _properties_ defined in
        [Thorlabs][msl.equipment_resources.thorlabs.thorlabs.Thorlabs].

        Attributes: Connection Properties:
            actuator (str | None): The actuator that is attached to the motor controller.
                If not specified, the value is looked up in a file that is managed by
                Thorlabs software. If the Thorlabs file cannot be found, an exception is
                raised. _Default: `None`_
        """
        super().__init__(equipment)

        device = find_device(equipment)
        if not device:
            msg = (
                "Cannot determine the actuator that is attached to the motor controller. "
                "Specify an 'actuator' key in the Connection properties with the value as "
                "the model number of the actuator that is attached to the motor controller."
            )
            raise MSLConnectionError(self, msg)

        match = re.search(r"(?P<number>\d+)", device)
        if match is None:
            msg = f"Do not know how to configure the actuator type for {device!r}"
            raise MSLConnectionError(self, msg)

        typ = int(match["number"])

        self._is_slot_system: bool = False
        self._has_encoder: bool = False  # EncoderFitted false
        self._position_message_id: int = 0x0411

        if "ZFS" in device:
            _configure_zfs(self)
            #  6mm: ZFS06
            # 13mm: ZFS13, ZFS13B
            # 25mm: ZFS25B
            actuator = {6: 0x40, 13: 0x41, 25: 0x42}[typ]
        elif "ZST" in device:
            _configure_zst(self)
            #  6mm: ZST206, ZST6B, ZST6
            # 13mm: ZST213B, ZST213, ZST13B, ZST13
            # 25mm: ZST225B, ZST25B, ZST25
            actuator = {6: 0x30, 206: 0x30, 13: 0x31, 213: 0x31, 25: 0x32, 225: 0x32}[typ]
        else:
            msg = f"The actuator {device!r} is not currently supported, only ZFS and ZST series are"
            raise MSLConnectionError(self, msg)

        _ = self.write(0x04FE, param1=actuator, dest=0x50)  # MGMSG_MOT_SET_TSTACTUATORTYPE


def _configure_zfs(kst: KST) -> None:
    steps = 24.0 * 2048.0 * 400.0 / 9.0
    kst._position = Convert(1.0 / steps, decimals=6)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    kst._velocity = Convert(1.0 / (steps * 53.68), decimals=3)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    kst._acceleration = Convert((1.0 * 90.9) / steps, decimals=3)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

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


def _configure_zst(kst: KST) -> None:
    steps = 24.0 * 2048.0 * 40.866
    kst._position = Convert(1.0 / steps, decimals=6)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    kst._velocity = Convert(1.0 / (steps * 53.68), decimals=3)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    kst._acceleration = Convert((1.0 * 90.9) / steps, decimals=3)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

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
