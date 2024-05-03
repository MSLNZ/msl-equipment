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

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        super(PTB330, self).__init__(record)
        print("using PTB330 class")

    def set_units(self, *, celcius: bool = True, p_unit: tuple[str, str] = ('P', 'hPa')) -> None:
        """Set units to be metric or non-metric, and/or set the desired pressure unit

        :param celcius: True for metric units (ºC), or False for non-metric (ºF)
            here also allowed K!
        :param p_unit: a tuple of the pressure quantity (e.g. P, P3h, P1, P2, etc), and a unit from
            [        allowed_units = [
            'hPa', 'psia', 'inHg', 'torr', 'bara', 'barg', 'psig', 'mbar', 'mmHg', 'kPa', 'Pa', 'mmH2O', 'inH2O'
        ]]
        :return:
        """
        allowed_quantities_units = {}
        self.write("UNIT ??")
        for i in range(6 + len(self.pressure_modules)):
            reply = self.read()
            list_unit = [_u.strip() for _u in reply.split(":")]
            allowed_quantities_units[list_unit[0]] = list_unit[1]

        # Pressure
        if not p_unit[0] in allowed_quantities_units:
            self.log_error(f"{p_unit[0]} not a known quantity on device")
            return
        if p_unit[1] in allowed_quantities_units[p_unit[0]]:
            reply = self.query(f"UNIT {p_unit[0]} {p_unit[1]}")
            list_unit = [_u.strip() for _u in reply.split(":")]
            self.units[list_unit[0]] = list_unit[1]
            for i in range(5 + len(self.pressure_modules)):
                reply = self.read()
                list_unit = [_u.strip() for _u in reply.split(":")]
                self.units[list_unit[0]] = list_unit[1]

            if p_unit[0] in self.units:
                if not self.units[p_unit[0]] == p_unit[1]:
                    self.check_for_errors()
            else:
                self.log_error(f"{p_unit[0]} unit not set correctly. Units are {self.units}")
        else:
            self.log_error(f"{p_unit[1]} is not an allowed unit {allowed_quantities_units[p_unit[0]]}")

#TODO: allow setting of temperature units for this device!

