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


@register(manufacturer=r'Vaisala', model=r'PTB330', flags=re.IGNORECASE)
class PTB330(PTU300):

    def __init__(self, record: EquipmentRecord) -> None:
        """Vaisala Barometer PTB330 series.
        Device manual: https://docs.vaisala.com/v/u/M210796EN-J/en-US

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        super(PTB330, self).__init__(record)

    def set_units(self, desired_units: dict[str, str]) -> None:
        """Set units of specified quantities

        :param desired_units: dictionary of quantities and units as specified in the instrument manual on page 15.
            These may include the following (available options depend on the barometer components):
            Pressure quantities: P, P3h, P1, P2, QNH, QFE, HCP, ...
            Pressure units: hPa, psi, inHg, torr, bar, mbar, mmHg, kPa, Pa, mmH2O, inH2O
            Temperature quantities: T, TP1, TP2, TP3, ...
            Temperature units: °C, °F, K (as 'C, 'F, or K)
        """
        allowed_quantities_units = {}
        self.write("UNIT ??")  # list the available measurement units for the quantities
        for i in range(6 + len(self.pressure_modules)):
            reply = self.read()
            list_unit = [_u.strip() for _u in reply.split(":")]
            allowed_quantities_units[list_unit[0]] = list_unit[1]

        for quantity, u in desired_units.items():
            if quantity not in allowed_quantities_units:
                self.log_error(f'{quantity} is not a known quantity on this {self.info["Model"]} device. '
                      f'Please select from {[i for i in allowed_quantities_units.keys()]}')
                return
            if u in allowed_quantities_units[quantity]:
                reply = self.query(f"UNIT {quantity} {u}")
                list_unit = [_u.strip() for _u in reply.split(":")]
                self.units[list_unit[0]] = list_unit[1]
                for i in range(5 + len(self.pressure_modules)):
                    reply = self.read()
                    list_unit = [_u.strip() for _u in reply.split(":")]
                    self.units[list_unit[0]] = list_unit[1]
                if quantity in self.units:
                    if not self.units[quantity] == u:
                        self.check_for_errors()
                else:
                    self.log_error(f"{quantity} unit not set correctly. Units are {self.units}")
            else:
                self.log_error(f"{u} is not an allowed unit. Please select from: {allowed_quantities_units[quantity]}.")
