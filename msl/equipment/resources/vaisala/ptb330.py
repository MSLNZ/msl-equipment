"""
Vaisala Barometer of type PTB330.
The PTB330 barometer is available with one, two, or three barometer modules.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from msl.equipment import EquipmentRecord
from msl.equipment.resources import register

from .ptu300 import PTU300


@register(manufacturer=r'Vaisala', model=r'^PTB330$', flags=re.IGNORECASE)
class PTB330(PTU300):

    def __init__(self, record: EquipmentRecord) -> None:
        """Vaisala Barometer PTB330 series.
        Device manual is available `here <https://docs.vaisala.com/v/u/M210855EN-D/en-US>`_.

        .. note::
            Ensure the device is in STOP or SEND mode before initiating a connection to a PC.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        super(PTB330, self).__init__(record)

    def set_units(self, desired_units: dict[str, str]) -> None:
        """Set units of specified quantities.

        :param desired_units: Dictionary of quantities (as keys) and their unit (their value)
            as specified in the instrument manual on pages 15 and 73.

            These may include the following (available options depend on the barometer components):

                * Pressure quantities: P, P3h, P1, P2, QNH, QFE, HCP, ...
                * Pressure units: hPa, psi, inHg, torr, bar, mbar, mmHg, kPa, Pa, mmH2O, inH2O
                * Temperature quantities: T, TP1, TP2, TP3, ...
                * Temperature units: 'C, 'F, or K (C and F are also supported but are returned as 'C or 'F)
        """
        allowed_quantities_units = {}
        self.write("UNIT ??")  # list the available measurement units for the quantities
        for i in range(6 + len(self._pressure_modules)):
            reply = self.read()
            _q, _u = [qu.strip() for qu in reply.split(":")]
            allowed_quantities_units[_q] = _u

        for quantity, u in desired_units.items():
            if quantity not in allowed_quantities_units:
                self.raise_exception(f'{quantity} is not a known quantity on this {self._info["Model"]} device. '
                      f'Please select from: {", ".join(allowed_quantities_units)}.')
            if u in allowed_quantities_units[quantity]:
                if u in ["C", "F"]:
                    u = "'" + u
                self.write(f"UNIT {quantity} {u}")
                for i in range(6 + len(self._pressure_modules)):
                    reply = self.read()
                    _q, _u = [qu.strip() for qu in reply.split(":")]
                    self._units[_q] = _u
                if quantity in self._units:
                    if not self._units[quantity] == u:
                        self.raise_exception(f"{quantity} unit '{u}' not set correctly. Current units are {self._units}")
                else:
                    self.raise_exception(f"{quantity} unit '{u}' not set correctly. Current units are {self._units}")
            else:
                self.raise_exception(f'{u} is not an allowed unit. '
                                     f'Please select from: {", ".join(allowed_quantities_units[quantity].split())}.')
