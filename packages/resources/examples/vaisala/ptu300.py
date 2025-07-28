"""
Example showing how to communicate with a Vaisala Barometer which reads pressure, temperature, and relative humidity,
e.g. of type PTU300
"""
from pprint import pprint

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
)

record = EquipmentRecord(
    manufacturer='Vaisala',
    model='PTU300',
    serial='P4040154',
    connection=ConnectionRecord(
        address='COM3',  # change for your device
        timeout=5,
    )
)

vaisala = record.connect()

# display information about the device
pprint(vaisala.device_info)

vaisala.check_for_errors()

desired_units = {
    "P":    'hPa',
    "P3h":  'hPa',
    "T":    "'C",
    "RH":   "%RH"
}
vaisala.set_units(desired_units=desired_units)
print("Units set:", vaisala.units)

format = '4.3 P " " U5 " " 3.3 T " " U5" "  3.3 RH " " U5" "  SN " " #r #n'
vaisala.set_format(format=format)

# There are two ways to check the format string that has been set
print(vaisala.get_format())
print(vaisala.device_info["Output format"])

# Get reading from device
print(vaisala.get_reading_str())

vaisala.disconnect()
