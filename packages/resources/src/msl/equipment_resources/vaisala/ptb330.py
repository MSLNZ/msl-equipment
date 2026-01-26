"""[Vaisala](https://www.vaisala.com/en){:target="_blank"} PTB330 Barometer.

The PTB330 barometer is available with one, two, or three barometer modules.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from msl.equipment.interfaces import MSLConnectionError

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment

from .ptu300 import PTU300


class PTB330(PTU300, manufacturer=r"Vaisala", model=r"^PTB330$", flags=re.IGNORECASE):
    """[Vaisala](https://www.vaisala.com/en){:target="_blank"} PTB330 Barometer."""

    def __init__(self, equipment: Equipment) -> None:
        """Vaisala PTB330 Barometer.

        The device manual is available [here](https://docs.vaisala.com/r/M210855EN-E/en-US){:target="_blank"}.

        The default settings for the RS232 connection are:

        * Baud rate: 4800
        * Data bits: 7
        * Parity: EVEN

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Vaisala"
        model=r"^PTB330$"
        flags=IGNORECASE
        ```

        !!! warning
            Ensure the device is in `STOP` or `SEND` mode before initiating communication.

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)

    def set_units(self, desired_units: dict[str, str]) -> None:  # pyright: ignore[reportImplicitOverride]
        """Set units of specified quantities.

        Args:
            desired_units: Dictionary of *quantity* (as keys) and their *unit* (as values)
                as specified in the instrument manual on pages 12 and 68.

                These may include the following (available options depend on the barometer components):

                * Pressure *quantity*: P, P3h, P1, P2, QNH, QFE, HCP, ...
                * Pressure *unit*: hPa, psi, inHg, torr, bar, mbar, mmHg, kPa, Pa, mmH2O, inH2O
                * Temperature *quantity*: T, TP1, TP2, TP3, ...
                * Temperature *unit*: 'C, 'F, or K (C and F are also supported but are returned as 'C or 'F)
        """
        allowed_quantities_units: dict[str, str] = {}
        _ = self.write("UNIT ??")  # list the available measurement units for the quantities
        for _ in range(6 + len(self._pressure_modules)):
            reply = self.read()
            _q, _u = [qu.strip() for qu in reply.split(":")]
            allowed_quantities_units[_q] = _u

        for quantity, unit in desired_units.items():
            if quantity not in allowed_quantities_units:
                msg = (
                    f"{quantity} is not a known quantity on this {self._info['Model']} device.\n"
                    f"Please select from: {', '.join(allowed_quantities_units)}"
                )
                raise MSLConnectionError(self, msg)

            if unit in allowed_quantities_units[quantity]:
                if unit in ["C", "F"]:
                    unit = "'" + unit  # noqa: PLW2901

                _ = self.write(f"UNIT {quantity} {unit}")
                for _ in range(6 + len(self._pressure_modules)):
                    reply = self.read()
                    _q, _u = [qu.strip() for qu in reply.split(":")]
                    self._units[_q] = _u

                if quantity in self._units:
                    if self._units[quantity] != unit:
                        msg = f"{quantity} unit '{unit}' not set correctly. Current units are {self._units}"
                        raise MSLConnectionError(self, msg)
                else:
                    msg = f"{quantity} unit '{unit}' not set correctly. Current units are {self._units}"
                    raise MSLConnectionError(self, msg)
            else:
                msg = (
                    f"{unit} is not an allowed unit. "
                    f"Please select from: {', '.join(allowed_quantities_units[quantity].split())}"
                )
                raise MSLConnectionError(self, msg)
