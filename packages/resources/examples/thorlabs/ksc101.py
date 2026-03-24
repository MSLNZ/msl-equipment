"""Communicate with a KSC101 (KCube Solenoid) with a SH05 (shutter) attached."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import KSC

# You may want to replace "FTDI2" with "FTDI" if you are not using the Kinesis or XA software.
# Using "FTDI2" requires the D2XX driver to be installed for the solenoid controller.
# Using "FTDI" requires a libusb-compatible driver to be installed for the solenoid controller.
# Update 68000297 with the serial number of your solenoid controller.
connection = Connection(
    "FTDI2::0x0403::0xfaf0::68000297",
    manufacturer="Thorlabs",
    model="KSC101",
    serial="68000297",
    timeout=5,
    # init=True,  # If you want to initialise the solenoid controller to default parameters
)

# Connect to the controller
controller: KSC = connection.connect()

# Print information about the controller
print(controller.hardware_info())
print(f"Operating mode: {controller.operating_mode!r}")
print(f"Cycle parameters: {controller.get_cycle_parameters()}")
print(f"Display parameters: {controller.get_display_parameters()}")
print(f"Trigger parameters: {controller.get_trigger_parameters()}")

# Check the position of the safety key
if not controller.is_key_unlocked():
    print("WARNING! The safety key is in the locked position, shutter will not open")

# Set the operating mode to MANUAL
controller.operating_mode = controller.OperatingMode.MANUAL

# Open the shutter
controller.open_shutter()

time.sleep(2)

# Close the shutter
controller.close_shutter()

# Disconnect from the controller
controller.disconnect()
