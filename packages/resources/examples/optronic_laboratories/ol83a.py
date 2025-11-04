"""Example showing how to communicate with an Optronic Laboratories 83A DC Current Source."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import OLxxA


connection = Connection(
    "COM3",  # update for your current source
    manufacturer="Optronic Laboratories",
    model="83A",
    # address=1,  # internal address of device (optional)
)

# Connect to the current source
ol83a: OLxxA = connection.connect()

# Turn the output off
ol83a.turn_off()

# Select a lamp
ol83a.select_lamp(9)

# Get target information: lamp number, target value, target unit
print(f"target info: {ol83a.target_info()}")

# Get the output state (on or off)
print(f"is the output on? {ol83a.state()}")

# Set the target current
actual = ol83a.set_current(0.2345)
print(f"the actual current that was set is {actual}")

# Get the system status byte of the latest command that was executed
print(f"system status byte: {ol83a.system_status_byte:b}")

# Read the output current, voltage and wattage
print(f"output current is {ol83a.get_current()} A")
print(f"output voltage is {ol83a.get_voltage()} V")
print(f"output wattage is {ol83a.get_wattage()} W")

# Get the number of hours for lamp 9
hours = ol83a.get_option(9, 40)
print(f"hours: {hours}")

# Disconnect from the current source
ol83a.disconnect()
