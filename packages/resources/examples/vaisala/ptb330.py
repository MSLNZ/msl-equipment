"""Example showing how to communicate with a Vaisala PTB330 Barometer."""

from __future__ import annotations

from pprint import pprint
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import PTB330


connection = Connection(
    "COM3",  # update for your device
    manufacturer="Vaisala",
    model="PTB330",
    serial="L2310094",
)

# Connect to the device
ptb: PTB330 = connection.connect()

# Display information about the device
pprint(ptb.device_info)

# A mapping between a quantity and the unit to use for the quantity
ptb.set_units({"P": "hPa", "P3h": "mbar", "TP1": "'C"})
print("Units set:", ptb.units)

# Set the format that data will be returned as
ptb.set_format('4.3 P " " 4.3 P3h " " 2.1 TP1 #r #n')

# There are two ways to check the format string that has been set
print(ptb.get_format())
print(ptb.device_info["Output format"])

# Get a reading from the device (in the specified format)
print(ptb.get_reading_str())

# Disconnect from the device
ptb.disconnect()
