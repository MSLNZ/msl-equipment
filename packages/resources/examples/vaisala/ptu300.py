"""Example showing how to communicate with a Vaisala PTU300-series Barometer."""

from __future__ import annotations

from pprint import pprint
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import PTU300


connection = Connection(
    "COM3",  # update for your device
    manufacturer="Vaisala",
    model="PTU300",
    serial="P4040154",
)

# Connect to the device
ptu: PTU300 = connection.connect()

# Display information about the device
pprint(ptu.device_info)

# A mapping between a quantity and the unit to use for the quantity
ptu.set_units({"P": "hPa", "P3h": "hPa", "T": "'C", "RH": "%RH"})
print("Units set:", ptu.units)

# Set the format that data will be returned as
ptu.set_format('4.3 P " " U5 " " 3.3 T " " U5" "  3.3 RH " " U5" "  SN " " #r #n')

# There are two ways to check the format string that has been set
print(ptu.get_format())
print(ptu.device_info["Output format"])

# Get a reading from the device (in the specified format)
print(ptu.get_reading_str())

# Disconnect from the device
ptu.disconnect()
