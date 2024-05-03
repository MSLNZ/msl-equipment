"""
Example showing how to communicate with a Vaisala Barometer which reads pressure, temperature, and relative humidity,
e.g. of type PTU300
"""
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.constants import (
    Parity,
    DataBits,
)

import logging
logging.basicConfig(level=logging.INFO)

record = EquipmentRecord(
    manufacturer='Vaisala',
    model='PTU300',
    serial='P4040154',
    connection=ConnectionRecord(
        address='COM9',  # change for your device
        backend=Backend.MSL,
        baud_rate=4800,  # change for your device
        parity=Parity.EVEN,  # change for your device
        termination='\r\n',
        timeout=5,
        data_bits=DataBits.SEVEN,
    )
)

vaisala = record.connect()
vaisala.device_info()
print(vaisala.pressure_modules)
print(len(vaisala.pressure_modules))

vaisala.check_for_errors()

print(vaisala.units)
vaisala.set_units(celcius=True, p_unit=("P3h", 'hPa'))
print(vaisala.units)

# format = '4.3 P " " 3.3 T " " 3.3 RH " " SN " " #r #n'
# vaisala.set_format(format=format)

# print(vaisala.get_format())

print(vaisala.get_reading_str())


