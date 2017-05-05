"""
Rather than loading a PicoScope from an Equipment-Register database, manually create an 
EquipmentRecord for a PicoScope.
"""
from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

record = EquipmentRecord(
    manufacturer='Pico Technology',
    model='5244B',
    serial='DY135/055',
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::PicoScope5000A::ps5000a',
        properties={
            'resolution': '14bit',  # only used for ps5000a series PicoScope's
            'auto_select_power': True,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        },
    )
)
