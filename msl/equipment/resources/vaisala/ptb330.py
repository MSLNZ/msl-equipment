"""
Vaisala Barometer which reads pressure only, e.g. of type PTB330
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

    def set_units(self, metric: bool = True, p_unit: str = 'hPa') -> None:
        print(self.query("UNIT ??"))
        print(self.read())
        print(self.read())
        print(self.read())
        print(self.read())
        print(self.read())
        print(self.read())

     # todo - may wish to reverse the classes as there's only the pressure units to set here

