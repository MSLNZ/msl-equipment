"""
Rather than loading a PicoScope from an Equipment-Register database, manually create an 
EquipmentRecord for a PicoScope.
"""
from msl.equipment.constants import Backend
from msl.equipment import EquipmentRecord, ConnectionRecord

record = EquipmentRecord(
    manufacturer='Pico Technology',
    model='5244B',
    serial='DY135/055',
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::PicoScope5000A::ps5000a',
        properties={'open_unit': True, 'resolution': '14bit', 'auto_select_power': True},
    )
)

# auto_select_power -> for PicoScopes that can be powered by an AC adaptor or by a USB cable
# resolution -> only used for ps5000a series PicoScope's
